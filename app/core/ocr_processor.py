"""
app/core/ocr_processor.py

OCR wrapper với hardware auto-detection:
  macOS  → PaddleOCR (ổn định, CoreML acceleration qua onnxruntime-silicon)
  Windows + DirectML available → RapidOCR, use_dml=True  (GPU)
  Windows CPU-only             → RapidOCR, use_dml=False (CPU)

Lý do không dùng PaddleOCR trên Windows:
  Models bundle từ Linux/Mac có fused_conv2d OneDNN ops bake vào graph.
  Paddle lazy-compile static graph lần đầu inference → NotFoundError
  trên Windows OneDNN context. Env flags không có tác dụng vì ops nằm
  trong model file, không phải runtime config.

RapidOCR dùng cùng ONNX runtime với InsightFace nên không conflict DML.
"""

import sys
import logging
import numpy as np
import cv2
from typing import List, Dict


def _suppress_paddle_logs():
    for name in ["ppocr", "paddle", "paddleocr", "PIL", "pdfminer", "imghdr"]:
        logging.getLogger(name).setLevel(logging.ERROR)


def _detect_windows_ocr_provider() -> tuple[bool, str]:
    """
    Detect xem Windows có DirectML không.
    Returns: (use_dml: bool, reason: str)
    """
    try:
        import onnxruntime as ort
        available = ort.get_available_providers()
        if "DmlExecutionProvider" in available:
            return True, "Windows + DirectML → RapidOCR GPU (DML)"
        return False, "Windows CPU-only → RapidOCR CPU"
    except Exception:
        return False, "Windows onnxruntime detect failed → RapidOCR CPU"


class OCRProcessor:
    def __init__(self, lang: str = "en"):
        if sys.platform == "win32":
            self._init_rapidocr()
        else:
            self._init_paddleocr(lang)

    # ------------------------------------------------------------------
    # Windows: RapidOCR — reuse onnxruntime-directml, auto GPU/CPU
    # ------------------------------------------------------------------
    def _init_rapidocr(self):
        print("[GPU Check] Đang khởi tạo PaddleOCR...", flush=True)
        use_dml, reason = _detect_windows_ocr_provider()
        print(f"[GPU Check] OCR provider: {reason}", flush=True)

        from rapidocr_onnxruntime import RapidOCR
        self._engine = "rapid"
        # use_dml kwarg được forward vào config của cả Det/Cls/Rec sub-models
        self._rapid = RapidOCR(use_dml=use_dml)
        print("[GPU Check] PaddleOCR đã khởi tạo xong.", flush=True)

    # ------------------------------------------------------------------
    # macOS / Linux: PaddleOCR — giữ nguyên, không đụng
    # ------------------------------------------------------------------
    def _init_paddleocr(self, lang: str):
        _suppress_paddle_logs()
        sys.setrecursionlimit(50000)
        from paddleocr import PaddleOCR
        self._engine = "paddle"
        self._ocr = PaddleOCR(lang=lang, use_angle_cls=False, show_log=False)
        print("[GPU Check] PaddleOCR đã khởi tạo xong.", flush=True)

    # ------------------------------------------------------------------
    # Public API — output format giống nhau trên mọi platform
    # ------------------------------------------------------------------
    def get_text(self, img_array: np.ndarray) -> List[Dict]:
        """
        Detect text in image.
        Returns: [{'text': str, 'bbox': [[x,y]x4], 'score': float}]
        """
        if self._engine == "rapid":
            return self._get_text_rapid(img_array)
        return self._get_text_paddle(img_array)

    def _get_text_rapid(self, img_array: np.ndarray) -> List[Dict]:
        result, _ = self._rapid(img_array)
        if not result:
            return []
        output = []
        for item in result:
            # RapidOCR format: [bbox_points, text, score]
            bbox, text, score = item[0], item[1], item[2]
            output.append({
                "text": text,
                "bbox": bbox if isinstance(bbox, list) else bbox.tolist(),
                "score": float(score),
            })
        return output

    def _get_text_paddle(self, img_array: np.ndarray) -> List[Dict]:
        result = self._ocr.ocr(img_array)
        if not result or len(result) == 0 or result[0] is None:
            return []
        output = []
        res = result[0]
        if isinstance(res, dict):
            for text, score, bbox in zip(
                res.get("rec_texts", []),
                res.get("rec_scores", []),
                res.get("rec_polys", []),
            ):
                output.append({
                    "text": text,
                    "bbox": bbox.tolist() if hasattr(bbox, "tolist") else bbox,
                    "score": float(score),
                })
        else:
            for line in res:
                if line:
                    points, (text, score) = line[0], line[1]
                    output.append({"text": text, "bbox": points, "score": float(score)})
        return output

    def get_text_from_file(self, image_path: str) -> List[Dict]:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        return self.get_text(img)
