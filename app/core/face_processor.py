"""
app/core/face_processor.py

FaceProcessor: InsightFace wrapper.
"""

import logging
import numpy as np
from typing import List

from app.core.config import settings

logger = logging.getLogger(__name__)

class FaceProcessor:
    def __init__(self):
        try:
            import insightface
        except ImportError as e:
            raise ImportError(
                "insightface chưa cài. Chạy: uv pip install insightface"
            ) from e

        import os
        os.environ.setdefault("OMP_NUM_THREADS", "4")

        provider = settings.ONNX_PROVIDER
        ctx_id = settings.INSIGHTFACE_CTX_ID
        models_root = str(settings.MODELS_ROOT)

        self._app = insightface.app.FaceAnalysis(
            name=settings.INSIGHTFACE_MODEL_NAME,
            root=models_root,
            providers=[provider],
        )
        self._app.prepare(ctx_id=ctx_id, det_size=settings.DET_SIZE)
        self._provider = provider

        logger.info("FaceProcessor sẵn sàng — provider: %s", self._provider)

    @property
    def provider(self) -> str:
        return self._provider

    def get_embedding(self, img_array: np.ndarray) -> List[dict]:
        """
        Detect faces trong 1 frame.

        Args:
            img_array: BGR image (OpenCV format)

        Returns:
            List[{embedding, bbox, det_score}]
        """
        faces = self._app.get(img_array)
        return [
            {
                "embedding": face.embedding,
                "bbox": face.bbox.astype(int).tolist(),
                "det_score": float(face.det_score),
            }
            for face in faces
            if float(face.det_score) >= settings.FACE_DET_SCORE_THRESHOLD
        ]

    def get_embedding_from_file(self, image_path: str) -> List[dict]:
        """
        Load ảnh từ path và trả về face embeddings.

        Raises:
            ValueError: nếu không đọc được ảnh
        """
        import cv2

        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Không đọc được ảnh: {image_path}")
        return self.get_embedding(img)

    def get_embeddings_batch(self, frames: List[np.ndarray]) -> List[List[dict]]:
        """
        Batch inference: chạy get_embedding trên list frames.

        Args:
            frames: List[BGR numpy array]

        Returns:
            List[List[{embedding, bbox, det_score}]] — 1 list per frame
        """
        return [self.get_embedding(frame) for frame in frames]
