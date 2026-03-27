import insightface
import numpy as np
import cv2
from typing import List, Optional
from app.core.config import settings

class FaceProcessor:
    def __init__(self):
        # Initialize FaceAnalysis with 'buffalo_l' model pack (includes detection and recognition)
        # allowed_modules=None means load all (detection, recognition, etc.)
        self.app = insightface.app.FaceAnalysis(name='buffalo_l', root='./data/insightface_models')
        self.app.prepare(ctx_id=0, det_size=settings.DET_SIZE)

    def get_embedding(self, img_array: np.ndarray) -> List[dict]:
        """
        Detect faces in an image and return list of embeddings and bounding boxes.
        """
        faces = self.app.get(img_array)
        results = []
        for face in faces:
             results.append({
                 'embedding': face.embedding,
                 'bbox': face.bbox.astype(int).tolist(),
                 'det_score': float(face.det_score)
             })
        return results

    def get_embedding_from_file(self, image_path: str) -> List[dict]:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        return self.get_embedding(img)
