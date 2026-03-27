# This script is designed to be copied into a Google Colab cell.
# It contains all necessary classes and logic in a single file.

# --- INSTALLATION (Run in a separate cell in Colab) ---
# !pip install fastapi uvicorn opencv-python insightface onnxruntime faiss-cpu numpy python-multipart paddlepaddle paddleocr sentence-transformers pandas pyarrow
# !apt-get update && apt-get install -y libgl1-mesa-glx

import os
import cv2
import numpy as np
import json
import faiss
import pandas as pd
import uuid
from typing import List, Dict, Optional, Tuple
from glob import glob
from tqdm import tqdm
import insightface
from paddleocr import PaddleOCR
from sentence_transformers import SentenceTransformer

# --- CONFIGURATION ---
# Update this path to where your project/data folder is in Google Drive
try:
    from google.colab import drive
    BASE_DIR = "/content/drive/MyDrive/face-search-on-video-mvp"
except:
    BASE_DIR = "."

class Settings:
    # InsightFace
    DET_SIZE = (640, 640)
    MODEL_ROOT = os.path.join(BASE_DIR, "data/insightface_models")
    
    # FAISS
    VECTOR_DIM = 512
    INDEX_PATH = os.path.join(BASE_DIR, "data/index/index.faiss")
    METADATA_PATH = os.path.join(BASE_DIR, "data/index/metadata.parquet")
    
    # OCR & Text Search
    BIB_INDEX_PATH = os.path.join(BASE_DIR, "data/index/bib_index.faiss")
    BIB_METADATA_PATH = os.path.join(BASE_DIR, "data/index/bib_metadata.parquet")
    TEXT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    TEXT_EMBEDDING_DIM = 384
    
    # Video Processing
    FRAME_INTERVAL = 30
    VIDEO_DIR = os.path.join(BASE_DIR, "data/videos")

settings = Settings()

# Ensure directories exist
os.makedirs(os.path.dirname(settings.INDEX_PATH), exist_ok=True)
os.makedirs(settings.MODEL_ROOT, exist_ok=True)
os.makedirs(settings.VIDEO_DIR, exist_ok=True)

# --- CORE CLASSES ---

class FaceTracker:
    def __init__(self, similarity_threshold: float = 0.6, max_missed_frames: int = 2):
        self.active_tracks = []
        self.similarity_threshold = similarity_threshold
        self.max_missed_frames = max_missed_frames
        
    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return np.dot(emb1, emb2) / (norm1 * norm2)

    def update(self, faces: List[Dict], frame_idx: int, timestamp: float) -> List[Dict]:
        finished_tracks = []
        
        if not faces:
            for track in self.active_tracks:
                track['missed_frames'] += 1
        else:
            matches = [] 
            used_tracks = set()
            used_faces = set()
            
            for t_idx, track in enumerate(self.active_tracks):
                track_emb = track['best_face']['embedding']
                for f_idx, face in enumerate(faces):
                    score = self._cosine_similarity(track_emb, face['embedding'])
                    if score > self.similarity_threshold:
                        matches.append((t_idx, f_idx, score))
            
            matches.sort(key=lambda x: x[2], reverse=True)
            
            for t_idx, f_idx, score in matches:
                if t_idx in used_tracks or f_idx in used_faces:
                    continue
                
                track = self.active_tracks[t_idx]
                face = faces[f_idx]
                
                track['missed_frames'] = 0
                track['last_seen_frame_idx'] = frame_idx
                track['end_timestamp'] = timestamp
                track['history'].append(face)
                
                if face['det_score'] > track['best_face']['det_score']:
                     track['best_face'] = face
                
                used_tracks.add(t_idx)
                used_faces.add(f_idx)
            
            for f_idx, face in enumerate(faces):
                if f_idx not in used_faces:
                     self.active_tracks.append({
                         'id': str(uuid.uuid4()),
                         'best_face': face,
                         'start_timestamp': timestamp,
                         'end_timestamp': timestamp,
                         'last_seen_frame_idx': frame_idx,
                         'missed_frames': 0,
                         'history': [face]
                     })
            
            for t_idx, track in enumerate(self.active_tracks):
                if t_idx not in used_tracks:
                    track['missed_frames'] += 1
                    
        new_active = []
        for track in self.active_tracks:
            if track['missed_frames'] > self.max_missed_frames:
                finished_tracks.append(track)
            else:
                new_active.append(track)
        
        self.active_tracks = new_active
        return finished_tracks

    def finalize(self) -> List[Dict]:
        finished = list(self.active_tracks)
        self.active_tracks = []
        return finished

class FaceProcessor:
    def __init__(self):
        self.app = insightface.app.FaceAnalysis(name='buffalo_l', root=settings.MODEL_ROOT)
        self.app.prepare(ctx_id=0, det_size=settings.DET_SIZE)

    def get_embedding(self, img_array: np.ndarray) -> List[dict]:
        faces = self.app.get(img_array)
        results = []
        for face in faces:
             results.append({
                 'embedding': face.embedding,
                 'bbox': face.bbox.astype(int).tolist(),
                 'det_score': float(face.det_score)
             })
        return results

class OCRProcessor:
    def __init__(self, lang: str = 'en'):
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False, use_gpu=True)

    def get_text(self, img_array: np.ndarray) -> List[Dict]:
        result = self.ocr.ocr(img_array, cls=True)
        output = []
        if result and result[0]:
            for line in result[0]:
                points = line[0]
                text, score = line[1]
                output.append({
                    'text': text,
                    'bbox': points,
                    'score': score
                })
        return output

class VectorStore:
    def __init__(self, load_existing: bool = True):
        self.dimension = settings.VECTOR_DIM
        self.indices = [] 
        self.bib_indices = []
        
        if load_existing:
            self.load()
        else:
            self.indices.append((faiss.IndexFlatIP(self.dimension), []))
            self.bib_indices.append((faiss.IndexFlatIP(settings.TEXT_EMBEDDING_DIM), []))

    @property
    def index(self):
        return self.indices[0][0]

    @property
    def metadata(self):
        return self.indices[0][1]
        
    @property
    def bib_index(self):
        return self.bib_indices[0][0]

    @property
    def bib_metadata(self):
        return self.bib_indices[0][1]

    def add_vectors(self, vectors: np.ndarray, metadata_entries: List[Dict]):
        if vectors.shape[0] != len(metadata_entries):
            raise ValueError("Number of vectors and metadata entries must match.")
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self.metadata.extend(metadata_entries)

    def add_bib_vectors(self, vectors: np.ndarray, metadata_entries: List[Dict]):
        if vectors.shape[0] != len(metadata_entries):
            raise ValueError("Number of vectors and metadata entries must match.")
        faiss.normalize_L2(vectors)
        self.bib_index.add(vectors)
        self.bib_metadata.extend(metadata_entries)

    def save(self):
        os.makedirs(os.path.dirname(settings.INDEX_PATH), exist_ok=True)
        faiss.write_index(self.index, settings.INDEX_PATH)
        
        if self.metadata:
            df = pd.DataFrame(self.metadata)
            df.to_parquet(settings.METADATA_PATH, index=False)
        
        if self.bib_indices:
             faiss.write_index(self.bib_index, settings.BIB_INDEX_PATH)
             if self.bib_metadata:
                df = pd.DataFrame(self.bib_metadata)
                df.to_parquet(settings.BIB_METADATA_PATH, index=False)

    def load(self):
        print("Loading indices...")
        self.indices = []
        self.bib_indices = []
        
        shard_pattern = os.path.join(os.path.dirname(settings.INDEX_PATH), "shard_*")
        shard_dirs = sorted(glob(shard_pattern), key=lambda x: x) # simple sort
        
        if shard_dirs:
            print(f"Found {len(shard_dirs)} shards: {shard_dirs}")
            for d in shard_dirs:
                self._load_pair(d)
        else:
            if os.path.exists(settings.INDEX_PATH):
                print(f"Loading main index from {settings.INDEX_PATH}")
                self._load_pair(os.path.dirname(settings.INDEX_PATH), main_file=True)
            else:
                self.indices.append((faiss.IndexFlatIP(self.dimension), []))
                self.bib_indices.append((faiss.IndexFlatIP(settings.TEXT_EMBEDDING_DIM), []))

    def _load_pair(self, directory: str, main_file: bool = False):
        if main_file:
            idx_path = settings.INDEX_PATH
            meta_path = settings.METADATA_PATH
            bib_idx_path = settings.BIB_INDEX_PATH
            bib_meta_path = settings.BIB_METADATA_PATH
        else:
            idx_path = os.path.join(directory, "index.faiss")
            meta_path = os.path.join(directory, "metadata.parquet")
            bib_idx_path = os.path.join(directory, "bib_index.faiss")
            bib_meta_path = os.path.join(directory, "bib_metadata.parquet")

        try:
            if os.path.exists(idx_path):
                idx = faiss.read_index(idx_path)
                meta = []
                if os.path.exists(meta_path):
                    try:
                        df = pd.read_parquet(meta_path)
                        meta = json.loads(df.to_json(orient='records'))
                    except Exception as e:
                         pass
                self.indices.append((idx, meta))
        except Exception as e:
            print(f"Error loading face index ({idx_path}): {e}")

        try:
            if os.path.exists(bib_idx_path):
                bib_idx = faiss.read_index(bib_idx_path)
                bib_meta = []
                if os.path.exists(bib_meta_path):
                    try:
                        df = pd.read_parquet(bib_meta_path)
                        bib_meta = json.loads(df.to_json(orient='records'))
                    except Exception as e:
                         pass
                self.bib_indices.append((bib_idx, bib_meta))
            else:
                self.bib_indices.append((faiss.IndexFlatIP(settings.TEXT_EMBEDDING_DIM), []))
        except Exception as e:
             print(f"Error loading bib index ({bib_idx_path}): {e}")
             self.bib_indices.append((faiss.IndexFlatIP(settings.TEXT_EMBEDDING_DIM), []))


# --- PROCESSING LOGIC ---

def process_video(video_path: str, face_processor: FaceProcessor, ocr_processor: OCRProcessor, text_model: SentenceTransformer, vector_store: VectorStore, face_tracker: FaceTracker):
    print(f"Processing {video_path}...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video file {video_path}")
        return

    frame_count = 0
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    process_interval = settings.FRAME_INTERVAL 
    
    pbar = tqdm(total=total_frames)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        pbar.update(1)
        
        if frame_count % process_interval != 0:
            continue
            
        timestamp = frame_count / fps

        # --- Face Detection & Tracking ---
        current_faces = []
        try:
            faces = face_processor.get_embedding(frame)
            if faces:
                current_faces = faces
        except Exception as e:
            print(f"Error processing face frame {frame_count}: {e}")

        finished_tracks = face_tracker.update(current_faces, frame_count, timestamp)
        
        if finished_tracks:
            embeddings = []
            metadata_list = []
            for track in finished_tracks:
                best_face = track['best_face']
                embeddings.append(best_face['embedding'])
                metadata_list.append({
                    'video_path': video_path.replace(BASE_DIR, "data"), # Storage optimization: relative path
                    'timestamp': track['start_timestamp'],
                    'end_timestamp': track['end_timestamp'],
                    'frame_idx': track['last_seen_frame_idx'],
                    'bbox': best_face['bbox'],
                    'det_score': best_face['det_score'],
                    'type': 'face',
                    'track_id': track['id']
                })
            
            if embeddings:
                vector_store.add_vectors(np.array(embeddings), metadata_list)

        # --- OCR / Bib Detection ---
        if current_faces:
            try:
                for face in current_faces:
                    fx1, fy1, fx2, fy2 = [int(v) for v in face['bbox']]
                    fw = fx2 - fx1
                    fh = fy2 - fy1
                    
                    frame_h, frame_w = frame.shape[:2]
                    
                    cx1 = max(0, int(fx1 - fw * 0.5))
                    cx2 = min(frame_w, int(fx2 + fw * 0.5))
                    cy1 = min(frame_h, fy2)
                    cy2 = min(frame_h, int(fy2 + fh * 3.0))
                    
                    if cx2 <= cx1 or cy2 <= cy1:
                        continue
                        
                    chest_crop = frame[cy1:cy2, cx1:cx2]
                    
                    target_width = 320
                    scale = 1.0
                    if (cx2 - cx1) > target_width:
                        scale = target_width / (cx2 - cx1)
                        new_h = int((cy2 - cy1) * scale)
                        chest_crop = cv2.resize(chest_crop, (target_width, new_h))
                        
                    texts = ocr_processor.get_text(chest_crop)
                    
                    if texts:
                        bib_embeddings = []
                        bib_metadata_list = []
                        
                        for item in texts:
                             text_str = item['text']
                             if any(c.isdigit() for c in text_str):
                                emb = text_model.encode([text_str])[0]
                                
                                orig_bbox = []
                                for pt in item['bbox']:
                                    px, py = pt
                                    orig_x = int(cx1 + px / scale)
                                    orig_y = int(cy1 + py / scale)
                                    orig_bbox.append([orig_x, orig_y])
                                
                                bib_embeddings.append(emb)
                                bib_metadata_list.append({
                                    'video_path': video_path.replace(BASE_DIR, "data"),
                                    'timestamp': timestamp,
                                    'frame_idx': frame_count,
                                    'bbox': orig_bbox,
                                    'score': item['score'],
                                    'text': text_str,
                                    'type': 'bib'
                                })
                        
                        if bib_embeddings:
                            vector_store.add_bib_vectors(np.array(bib_embeddings), bib_metadata_list)

            except Exception as e:
                print(f"Error processing OCR for face in frame {frame_count}: {e}")
            
    # FORCE FINISH remaining tracks
    remaining_tracks = face_tracker.finalize()
    if remaining_tracks:
        embeddings = []
        metadata_list = []
        for track in remaining_tracks:
            best_face = track['best_face']
            embeddings.append(best_face['embedding'])
            metadata_list.append({
                'video_path': video_path.replace(BASE_DIR, "data"),
                'timestamp': track['start_timestamp'], 
                'end_timestamp': track['end_timestamp'],
                'frame_idx': track['last_seen_frame_idx'],
                'bbox': best_face['bbox'],
                'det_score': best_face['det_score'],
                'type': 'face',
                'track_id': track['id']
            })
        if embeddings:
            vector_store.add_vectors(np.array(embeddings), metadata_list)

    cap.release()
    pbar.close()

def load_processed_videos(processed_path: str) -> set:
    if os.path.exists(processed_path):
        with open(processed_path, 'r') as f:
            return set(json.load(f))
    return set()

def save_processed_video(processed_path: str, processed_videos: set):
    with open(processed_path, 'w') as f:
        json.dump(list(processed_videos), f)

# --- MAIN EXECUTION ---

def main():
    BATCH_SIZE = 5
    video_dir = settings.VIDEO_DIR
    processed_path = os.path.join(BASE_DIR, "data/processed_videos.json")

    print(f"BASE_DIR: {BASE_DIR}")
    print(f"VIDEO_DIR: {video_dir}")
    print(f"PROCESSED_LOG: {processed_path}")
    
    if not os.path.exists(video_dir):
        os.makedirs(video_dir)
        print(f"Created {video_dir}. Please put some videos there.")
        return
    
    print("Initializing models...")
    face_processor = FaceProcessor()
    ocr_processor = OCRProcessor()
    text_model = SentenceTransformer(settings.TEXT_EMBEDDING_MODEL)
    
    # We use settings.VIDEO_DIR not local var if not consistent, but here it is.
    video_files = glob(os.path.join(video_dir, "*.mp4")) + \
                  glob(os.path.join(video_dir, "*.avi")) + \
                  glob(os.path.join(video_dir, "*.mov"))
    
    if not video_files:
        print(f"No videos found in {video_dir}")
        return

    # Load checkpoint
    processed_videos = load_processed_videos(processed_path)
    print(f"Loaded {len(processed_videos)} processed videos from checkpoint.")
        
    print(f"Found {len(video_files)} videos. Processing in batches of {BATCH_SIZE}...")
    
    # Process in batches
    for i in range(0, len(video_files), BATCH_SIZE):
        batch_idx = i // BATCH_SIZE
        batch_videos = video_files[i : i + BATCH_SIZE]
        
        # Define shard paths
        shard_dir = os.path.join(BASE_DIR, f"data/index/shard_{batch_idx}")
        os.makedirs(shard_dir, exist_ok=True)
        
        # Override global settings for this batch
        settings.INDEX_PATH = os.path.join(shard_dir, "index.faiss")
        settings.METADATA_PATH = os.path.join(shard_dir, "metadata.parquet")
        settings.BIB_INDEX_PATH = os.path.join(shard_dir, "bib_index.faiss")
        settings.BIB_METADATA_PATH = os.path.join(shard_dir, "bib_metadata.parquet")
        
        # Initialize VectorStore w/ load_existing=True to resume
        vector_store = VectorStore(load_existing=True)
        
        shard_has_updates = False
        
        print(f"\n--- Batch {batch_idx}: Processing {len(batch_videos)} videos ---")
        
        for video_file in batch_videos:
            if video_file in processed_videos:
                print(f"Skipping already processed: {video_file}")
                continue
            
            # Tracker resets per video
            face_tracker = FaceTracker()
            process_video(video_file, face_processor, ocr_processor, text_model, vector_store, face_tracker)
            
            # Incremental Save
            vector_store.save()
            
            # Update Checkpoint
            processed_videos.add(video_file)
            save_processed_video(processed_path, processed_videos)
            
            shard_has_updates = True
            print(f"Saved progress for {video_file}")
            
        if shard_has_updates:
            print(f"Batch {batch_idx} completed and saved to {shard_dir}")
        else:
            print(f"Batch {batch_idx} already fully processed.")

    print("All batches processed.")
    
    # Cleanup checkpoint
    if os.path.exists(processed_path):
        os.remove(processed_path)
        print("Checkpoint file removed.")

if __name__ == "__main__":
    main()
