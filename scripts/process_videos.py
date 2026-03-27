import sys
import os
import cv2
import json
import numpy as np
from tqdm import tqdm
from glob import glob
from sentence_transformers import SentenceTransformer

# Add project root to path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.core.face_processor import FaceProcessor
from app.core.ocr_processor import OCRProcessor
from app.core.vector_store import VectorStore

from app.core.tracker import FaceTracker

def process_video(video_path: str, face_processor: FaceProcessor, ocr_processor: OCRProcessor, text_model: SentenceTransformer, vector_store: VectorStore, face_tracker: FaceTracker):
    print(f"Processing {video_path}...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video file {video_path}")
        return

    frame_count = 0
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Calculate step to match desired processing FPS (e.g. 1 FPS)
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
                # Faces are List[dict] with embedding, bbox, det_score
        except Exception as e:
            print(f"Error processing face frame {frame_count}: {e}")

        # Update Tracker
        # This will return tracks that have finished (video ended or track lost)
        finished_tracks = face_tracker.update(current_faces, frame_count, timestamp)
        
        # Save FINISHED tracks
        if finished_tracks:
            embeddings = []
            metadata_list = []
            for track in finished_tracks:
                best_face = track['best_face']
                embeddings.append(best_face['embedding'])
                metadata_list.append({
                    'video_path': video_path,
                    'timestamp': track['start_timestamp'], # or use 'best_face' timestamp if tracked?
                                                           # User said "1 embedding" per track.
                                                           # We can store start time to index.
                    'end_timestamp': track['end_timestamp'],
                    'frame_idx': track['last_seen_frame_idx'], # Just for ref
                    'bbox': best_face['bbox'],
                    'det_score': best_face['det_score'],
                    'type': 'face',
                    'track_id': track['id']
                })
            
            if embeddings:
                vector_store.add_vectors(np.array(embeddings), metadata_list)

        # --- OCR / Bib Detection ---
        # Optimization: Only run OCR on "chest" areas relative to detected faces
        # Note: Tracker might give us stable faces, but for OCR we still want to check
        # the current frame's faces (current_faces) because bib might be visible now.
        # So we stick to using 'current_faces' for OCR ROI.
        if current_faces:
            try:
                for face in current_faces:
                    # Face BBox: [x1, y1, x2, y2]
                    fx1, fy1, fx2, fy2 = [int(v) for v in face['bbox']]
                    fw = fx2 - fx1
                    fh = fy2 - fy1
                    
                    # Define Chest ROI
                    # Chest is typically below face, wider than face
                    # ROI: x1 - 0.5w, y2, x2 + 0.5w, y2 + 3h (clamped)
                    
                    frame_h, frame_w = frame.shape[:2]
                    
                    cx1 = max(0, int(fx1 - fw * 0.5))
                    cx2 = min(frame_w, int(fx2 + fw * 0.5))
                    cy1 = min(frame_h, fy2) # Start from chin
                    cy2 = min(frame_h, int(fy2 + fh * 3.0)) # Extend down 3x face height
                    
                    if cx2 <= cx1 or cy2 <= cy1:
                        continue
                        
                    chest_crop = frame[cy1:cy2, cx1:cx2]
                    
                    # Resize if too large (target width 320)
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
                                # Embed text
                                emb = text_model.encode([text_str])[0]
                                
                                # Map bbox back to original frame
                                orig_bbox = []
                                for pt in item['bbox']:
                                    px, py = pt
                                    orig_x = int(cx1 + px / scale)
                                    orig_y = int(cy1 + py / scale)
                                    orig_bbox.append([orig_x, orig_y])
                                
                                bib_embeddings.append(emb)
                                bib_metadata_list.append({
                                    'video_path': video_path,
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
                'video_path': video_path,
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

def main():
    BATCH_SIZE = 5
    video_dir = "data/videos"
    processed_path = "data/processed_videos.json"

    if not os.path.exists(video_dir):
        os.makedirs(video_dir)
        print(f"Created {video_dir}. Please put some videos there.")
        return
    
    print("Initializing models...")
    face_processor = FaceProcessor()
    ocr_processor = OCRProcessor()
    text_model = SentenceTransformer(settings.TEXT_EMBEDDING_MODEL)
    
    video_files = glob(os.path.join(video_dir, "*.mp4")) + glob(os.path.join(video_dir, "*.avi")) + glob(os.path.join(video_dir, "*.mov"))
    
    if not video_files:
        print("No videos found in data/videos")
        return

    # Load checkpoint
    processed_videos = load_processed_videos(processed_path)
    print(f"Loaded {len(processed_videos)} processed videos from checkpoint.")
        
    print(f"Found {len(video_files)} videos. Processing in batches of {BATCH_SIZE}...")
    
    # Process in batches
    for i in range(0, len(video_files), BATCH_SIZE):
        batch_idx = i // BATCH_SIZE
        batch_videos = video_files[i : i + BATCH_SIZE]
        print(f"\n--- Batch {batch_idx}: Processing {len(batch_videos)} videos ---")
        
        # Define shard paths
        shard_dir = f"data/index/shard_{batch_idx}"
        os.makedirs(shard_dir, exist_ok=True)
        
        # Override global settings for this batch
        # This works because VectorStore uses 'settings' module
        settings.INDEX_PATH = os.path.join(shard_dir, "index.faiss")
        settings.METADATA_PATH = os.path.join(shard_dir, "metadata.parquet")
        settings.BIB_INDEX_PATH = os.path.join(shard_dir, "bib_index.faiss")
        settings.BIB_METADATA_PATH = os.path.join(shard_dir, "bib_metadata.parquet")

        
        shard_has_updates = False
        
        print(f"\n--- Batch {batch_idx}: Processing {len(batch_videos)} videos ---")
        
        for video_file in batch_videos:
            if video_file in processed_videos:
                print(f"Skipping already processed: {video_file}")
                continue

            # Initialize VectorStore
            # load_existing=True allows resuming a partially processed shard
            vector_store = VectorStore(load_existing=True)
            
            # Create fresh tracker for each video
            face_tracker = FaceTracker()
            process_video(video_file, face_processor, ocr_processor, text_model, vector_store, face_tracker)
            
            # Incremental Save:
            # 1. Save VectorStore (Index + Metadata)
            vector_store.save()
            
            # 2. Update Checkpoint
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
