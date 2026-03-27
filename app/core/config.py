import os

class Settings:
    # InsightFace
    DET_SIZE = (640, 640)
    
    # FAISS
    VECTOR_DIM = 512  # InsightFace buffalo_l produces 512d embeddings
    INDEX_PATH = "data/index/index.faiss"
    METADATA_PATH = "data/index/metadata.parquet"
    
    # Video Processing
    FRAME_INTERVAL = 30 # Process 1 frame every 30 frames (approx 1 FPS for 30fps video)

    # OCR & Text Search
    BIB_INDEX_PATH = "data/index/bib_index.faiss"
    BIB_METADATA_PATH = "data/index/bib_metadata.parquet"
    TEXT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    TEXT_EMBEDDING_DIM = 384 # Dimension for all-MiniLM-L6-v2

settings = Settings()
