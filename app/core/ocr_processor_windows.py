"""
app/core/ocr_processor_windows.py

RapidOCR wrapper — Windows (DirectML GPU / CPU fallback)

Lý do không dùng PaddleOCR trên Windows:
  Models bundle từ Linux/Mac có fused_conv2d OneDNN ops bake vào graph.
  Paddle lazy-compile static graph lần đầu inference → NotFoundError
  trên Windows OneDNN context. Env flags không có tác dụng vì ops nằm
  trong model file, không phải runtime config.

RapidOCR dùng cùng ONNX runtime với InsightFace nên không conflict DML.
"""

import numpy as np
import cv2
from typing import List, Dict

import onnxruntime as ort
from rapidocr_onnxruntime import RapidOCR


def _detect_provider() -> tuple[bool, str]:
    """
    Detect xem Windows có DirectML không.
    Returns: (use_dml: bool, reason: str)
    """
    try:
        available = ort.get_available_providers()
        if "DmlExecutionProvider" in available:
            return True, "Windows + DirectML → RapidOCR GPU (DML)"
        return False, "Windows CPU-only → RapidOCR CPU"
    except Exception:
        return False, "Windows onnxruntime detect failed → RapidOCR CPU"


_use_dml, _reason = _detect_provider()


class OCRProcessor:
    def __init__(self, lang: str = "en"):
        print(f"[GPU Check] OCR provider: {_reason}", flush=True)
        print("[GPU Check] Đang khởi tạo RapidOCR...", flush=True)
        self._rapid = RapidOCR(use_dml=_use_dml)
        print("[GPU Check] RapidOCR đã khởi tạo xong.", flush=True)

    def get_text(self, img_array: np.ndarray) -> List[Dict]:
        """
        Detect text in image.
        Returns: [{'text': str, 'bbox': [[x,y]×4], 'score': float}]
        """
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

    def get_text_from_file(self, image_path: str) -> List[Dict]:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        return self.get_text(img)
