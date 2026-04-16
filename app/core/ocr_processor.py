"""
app/core/ocr_processor.py

PaddleOCR wrapper — compatible với paddleocr >= 3.x
"""

import logging
import numpy as np
import cv2
from typing import List, Dict

def _suppress_paddle_logs():
    """Suppress verbose PaddleOCR/PaddlePaddle logs."""
    for name in [
        "ppocr", "paddle", "paddleocr",
        "PIL", "pdfminer", "imghdr",
    ]:
        logging.getLogger(name).setLevel(logging.ERROR)

class OCRProcessor:
    def __init__(self, lang: str = "en"):
        _suppress_paddle_logs()
        from paddleocr import PaddleOCR

        self.ocr = PaddleOCR(lang=lang)

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
            rec_texts = res.get('rec_texts', [])
            rec_scores = res.get('rec_scores', [])
            rec_polys = res.get('rec_polys', [])

            for text, score, bbox in zip(rec_texts, rec_scores, rec_polys):
                output.append({
                    "text": text,
                    "bbox": bbox.tolist() if hasattr(bbox, 'tolist') else bbox,
                    "score": float(score),
                })
        else:
            for line in res:
                if line:
                    points = line[0]
                    text, score = line[1]
                    output.append({
                        "text": text,
                        "bbox": points,
                        "score": float(score),
                    })

        return output

    def get_text_from_file(self, image_path: str) -> List[Dict]:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        return self.get_text(img)
