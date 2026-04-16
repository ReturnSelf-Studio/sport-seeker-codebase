"""
app/core/config.py

Hardware acceleration: auto-detect ONNX Runtime provider tại startup.
Priority: CoreML (macOS arm64) > DirectML (Windows GPU) > CPU
"""

import platform
import sys
import os
from pathlib import Path

def _detect_onnx_provider() -> tuple:
    """
    Auto-detect best ONNX Runtime execution provider.
    Returns: (provider_str, reason_str)
    """
    system = platform.system()
    machine = platform.machine().lower()

    try:
        import onnxruntime as ort
        available = ort.get_available_providers()

        if system == "Darwin" and machine == "arm64":
            if "CoreMLExecutionProvider" in available:
                return "CoreMLExecutionProvider", "macOS Apple Silicon → CoreML"
            return "CPUExecutionProvider", "macOS arm64 nhưng CoreML không khả dụng → CPU"

        if system == "Windows":
            if "DmlExecutionProvider" in available:
                return "DmlExecutionProvider", "Windows → DirectML (GPU)"
            return "CPUExecutionProvider", "Windows nhưng DirectML không khả dụng → CPU"

        return "CPUExecutionProvider", f"{system} {machine} → CPU"

    except ImportError:
        return "CPUExecutionProvider", "onnxruntime chưa cài → CPU fallback"
    except Exception as e:
        return "CPUExecutionProvider", f"lỗi detect provider ({e}) → CPU fallback"

def _get_models_root() -> Path:
    """
    Models root: Ưu tiên đường dẫn custom từ Flutter, nếu không có fallback về ~/SportSeeker/models/
    """
    custom_path = os.environ.get("SPORT_SEEKER_MODELS_ROOT", "").strip()
    if custom_path and os.path.exists(custom_path):
        return Path(custom_path)

    root = Path.home() / "SportSeeker" / "models"
    root.mkdir(parents=True, exist_ok=True)
    return root

_ONNX_PROVIDER, _PROVIDER_REASON = _detect_onnx_provider()

class Settings:
    ONNX_PROVIDER: str = _ONNX_PROVIDER
    ONNX_PROVIDER_REASON: str = _PROVIDER_REASON

    @property
    def INSIGHTFACE_CTX_ID(self) -> int:
        return 0 if self.ONNX_PROVIDER != "CPUExecutionProvider" else -1

    MODELS_ROOT: Path = _get_models_root()
    INSIGHTFACE_MODEL_NAME: str = os.environ.get("SPORT_SEEKER_MODEL_NAME", "buffalo_l")

    DET_SIZE: tuple = (640, 640)
    FACE_DET_SCORE_THRESHOLD: float = 0.5

    VECTOR_DIM: int = 512
    INDEX_PATH: str = "data/index/index.faiss"
    METADATA_PATH: str = "data/index/metadata.parquet"

    FRAME_INTERVAL: int = 30
    MIN_FRAME_INTERVAL: int = 5
    MAX_FRAME_INTERVAL: int = 60

    BIB_INDEX_PATH: str = "data/index/bib_index.faiss"
    BIB_METADATA_PATH: str = "data/index/bib_metadata.parquet"
    TEXT_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    TEXT_EMBEDDING_DIM: int = 384

    IMAGE_EXTENSIONS: tuple = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff")

    def log_startup_info(self) -> None:
        print(f"[SportSeeker] ONNX Provider : {self.ONNX_PROVIDER}")
        print(f"[SportSeeker] Reason        : {self.ONNX_PROVIDER_REASON}")
        print(f"[SportSeeker] ctx_id        : {self.INSIGHTFACE_CTX_ID}")
        print(f"[SportSeeker] Models root   : {self.MODELS_ROOT}")

settings = Settings()
