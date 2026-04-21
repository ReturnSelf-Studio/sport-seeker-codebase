"""
app/core/ocr_processor_macos.py

PaddleOCR wrapper — macOS ARM64 (M1/M2/M3/M4)
Compatible với paddleocr >= 3.x
"""

import logging
import numpy as np
import cv2
from typing import List, Dict


def _suppress_paddle_logs():
    for name in ["ppocr", "paddle", "paddleocr", "PIL", "pdfminer", "imghdr"]:
        logging.getLogger(name).setLevel(logging.ERROR)


_suppress_paddle_logs()

import sys
sys.setrecursionlimit(50000)
from paddleocr import PaddleOCR


class OCRProcessor:
    def __init__(self, lang: str = "en"):
        print("[GPU Check] Đang khởi tạo PaddleOCR...", flush=True)
        self.ocr = PaddleOCR(lang=lang, use_angle_cls=False, show_log=False)
        print("[GPU Check] PaddleOCR đã khởi tạo xong.", flush=True)

    def get_text(self, img_array: np.ndarray) -> List[Dict]:
        """
        Detect text in image.
        Returns: [{'text': str, 'bbox': [[x,y]×4], 'score': float}]
        """
        result = self.ocr.ocr(img_array)

        output = []
        if not result or len(result) == 0 or result[0] is None:
            return output

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