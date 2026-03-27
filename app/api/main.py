from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from typing import Optional
import cv2
import numpy as np
import os
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.face_processor import FaceProcessor
from app.core.ocr_processor import OCRProcessor
from app.core.vector_store import VectorStore

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Global variables
face_processor = None
ocr_processor = None
text_model = None
vector_store = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load resources on startup
    global face_processor, ocr_processor, text_model, vector_store
    print("Loading models and index...")
    face_processor = FaceProcessor()
    ocr_processor = OCRProcessor()
    text_model = SentenceTransformer(settings.TEXT_EMBEDDING_MODEL)
    vector_store = VectorStore(load_existing=True)
    yield
    # Clean up resources on shutdown
    print("Shutting down...")

app = FastAPI(title="Face Search on Video MVP", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for videos
if not os.path.exists("data/videos"):
    os.makedirs("data/videos")
app.mount("/videos", StaticFiles(directory="data/videos"), name="videos")

@app.post("/search")
async def search(
    file: UploadFile = File(None),
    text: Optional[str] = Form(None),
    type: str = Form("face"), # 'face' or 'bib'
    k: int = 10
):
    """
    Search for a face or bib number in the indexed videos.
    """
    if not vector_store:
         raise HTTPException(status_code=503, detail="Service not ready")

    results = []

    candidate_k = k * 10 # Search more candidates to allow for deduplication

    if type == "face":
        if not face_processor:
             raise HTTPException(status_code=503, detail="Service not ready")
        if not file:
            raise HTTPException(status_code=400, detail="Image file is required for face search")
            
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Detect face in query image
        faces = face_processor.get_embedding(img)
        if not faces:
            raise HTTPException(status_code=400, detail="No face detected in the image")
        
        # Use the largest face (or first with highest score)
        target_face = max(faces, key=lambda x: x['det_score'])
        embedding = np.array([target_face['embedding']])
        
        # Search
        raw_results = vector_store.search(embedding, k=candidate_k)
        
        # Deduplicate by video (keep best score)
        unique_videos = {}
        for res in raw_results:
            vid = res['video_path']
            if vid not in unique_videos or res['score'] > unique_videos[vid]['score']:
                unique_videos[vid] = res
        
        results = list(unique_videos.values())
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:k]

    elif type == "bib":
        if not text_model:
             raise HTTPException(status_code=503, detail="Service not ready")
        
        if not text:
             raise HTTPException(status_code=400, detail="No bib number found in text or image")
             
        embedding = text_model.encode([text])            
        raw_results = vector_store.search_bib(np.array(embedding), k=candidate_k)
        
        unique_videos = {}
        for res in raw_results:
            vid = res['video_path']
            res['matched_text'] = text
            if vid not in unique_videos or res['score'] > unique_videos[vid]['score']:
                unique_videos[vid] = res
                
        results = list(unique_videos.values())
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:k]

    else:
        raise HTTPException(status_code=400, detail="Invalid search type")

    return {"results": results}

@app.get("/")
def root():
    return {"message": "Face & Bib Search API is running. Use /docs to test."}
