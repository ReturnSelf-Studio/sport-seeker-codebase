from paddleocr import PaddleOCR
import numpy as np
import cv2
from typing import List, Tuple, Dict

class OCRProcessor:
    def __init__(self, lang: str = 'en'):
        # Initialize PaddleOCR
        # use_angle_cls=True to correct orientation
        # enable_mkldnn=False to avoid "No allocator found" errors on some Mac environments
        self.ocr = PaddleOCR(
            use_angle_cls=True, 
            lang=lang, 
            show_log=False, 
            use_gpu=False,
            enable_mkldnn=False
        )

    def get_text(self, img_array: np.ndarray) -> List[Dict]:
        """
        Detect text in an image and return list of results.
        Result format: [{'text': '...', 'bbox': [[x1,y1], [x2,y2], ...], 'score': ...}]
        """
        # PaddleOCR expects image in RGB or BGR? OpenCV reads BGR. PaddleOCR handles it.
        # result = self.ocr.ocr(img_array, cls=True)
        # result is a list of lists (one for each image if batch, but here we pass one image)
        
        result = self.ocr.ocr(img_array, cls=True)
        
        output = []
        if result and result[0]:
            for line in result[0]:
                # line format: [points, (text, score)]
                # points: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                points = line[0]
                text, score = line[1]
                
                output.append({
                    'text': text,
                    'bbox': points, # List of 4 points
                    'score': score
                })
        return output

    def get_text_from_file(self, image_path: str) -> List[Dict]:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        return self.get_text(img)
