import asyncio
import json
import logging
import os
import sys
import threading
import time
import queue
import uuid
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import settings
from app.core.project_manager import ProjectManager
from app.core.vector_store import VectorStore

os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

FaceProcessor = None
OCRProcessor = None
SentenceTransformer = None

model_status = "loading"  
model_loading_message = "Đang chuẩn bị khởi tạo..." 

app = FastAPI(title="Sport Seeker Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pm = ProjectManager()

def write_checkpoint(msg):
    try:
        log_dir = Path(os.environ.get('APPDATA', '')) / "SportSeeker" / "logs" if sys.platform == 'win32' else Path.home() / "SportSeeker" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        # Ghi thêm dòng checkpoint với thời gian thực
        with open(log_dir / "checkpoints.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except:
        pass

def background_model_loader():
    global FaceProcessor, OCRProcessor, SentenceTransformer, model_status, model_loading_message
    try:
        write_checkpoint("==================================================")
        write_checkpoint("▶ BẮT ĐẦU NẠP AI MODELS")
        
        model_loading_message = "Đang nạp AI Models vào RAM/VRAM..."
        print(f"[Backend] {model_loading_message}", flush=True)
        sys.stderr.write("5%|\n")
        sys.stderr.flush()

        # 1. Text Embedding
        write_checkpoint("⏳ [1/3] Đang nạp Text Embedding...")
        model_loading_message = "Đang nạp mô hình Text Embedding (1/3)..."
        from sentence_transformers import SentenceTransformer as ST
        from app.core.config import settings
        SentenceTransformer = ST(settings.TEXT_EMBEDDING_MODEL)
        sys.stderr.write("35%|\n")
        sys.stderr.flush()
        write_checkpoint("✅ [1/3] XONG Text Embedding!")

        # 2. InsightFace
        write_checkpoint("⏳ [2/3] Đang nạp InsightFace...")
        model_loading_message = "Đang nạp mô hình khuôn mặt InsightFace (2/3)..."
        from app.core.face_processor import FaceProcessor as FP
        FaceProcessor = FP()
        sys.stderr.write("70%|\n")
        sys.stderr.flush()
        write_checkpoint("✅ [2/3] XONG InsightFace!")

        # 3. PaddleOCR
        write_checkpoint("⏳ [3/3] Đang nạp PaddleOCR...")
        model_loading_message = "Đang nạp mô hình đọc số BIB PaddleOCR (3/3)..."
        from app.core.ocr_processor import OCRProcessor as OP
        OCRProcessor = OP()
        sys.stderr.write("100%|\n")
        sys.stderr.flush()
        write_checkpoint("✅ [3/3] XONG PaddleOCR!")

        model_status = "ready"
        model_loading_message = "Khởi tạo AI Models thành công!"
        print("[Backend] Khởi tạo AI Models thành công!", flush=True)
        write_checkpoint("🎉 HOÀN TẤT TOÀN BỘ AI MODELS!")
        
    except Exception as e:
        print(f"[Backend] Lỗi khởi tạo models: {e}", flush=True)
        model_status = "error"
        model_loading_message = f"Lỗi khởi tạo AI: {str(e)}"
        write_checkpoint(f"❌ LỖI KHỞI TẠO: {str(e)}")

@app.on_event("startup")
def startup_event():
    threading.Thread(target=background_model_loader, daemon=True).start()

@app.get("/models/status")
def get_model_status():
    return {"status": model_status, "message": model_loading_message}

def zombie_killer(parent_pid: int):
    while True:
        try:
            if sys.platform == 'win32':
                import psutil
                if not psutil.pid_exists(parent_pid):
                    os._exit(0)
            else:
                if os.getppid() != parent_pid and os.getppid() == 1:
                    os._exit(0)
        except Exception:
            pass
        time.sleep(2)

parent_pid_str = os.environ.get("SPORT_SEEKER_PARENT_PID")
if parent_pid_str and parent_pid_str.isdigit():
    threading.Thread(target=zombie_killer, args=(int(parent_pid_str),), daemon=True).start()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def emit_log(msg: str):
    await manager.broadcast(json.dumps({"type": "log", "data": msg}))

async def emit_progress(done: int, total: int):
    await manager.broadcast(json.dumps({"type": "progress", "data": {"done": done, "total": total}}))

async def emit_stage(stage: str):
    await manager.broadcast(json.dumps({"type": "stage", "data": stage}))

class ProjectCreate(BaseModel):
    name: str
    source_dir: str
    event_date: str = ""
    notes: str = ""

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Backend is healthy"}

@app.post("/shutdown")
async def shutdown_server():
    def kill_me():
        time.sleep(0.5)
        os._exit(0)
    threading.Thread(target=kill_me, daemon=True).start()
    return {"status": "ok", "message": "Shutting down..."}

@app.get("/projects")
def get_projects():
    return {"projects": pm.list_projects()}

@app.post("/projects")
def create_project(req: ProjectCreate):
    p = pm.create_project(req.name, req.source_dir, req.event_date, req.notes)
    return {"project": p}

@app.delete("/projects/{project_id}")
def delete_project(project_id: str, delete_files: bool = False):
    success = pm.delete_project(project_id, delete_files)
    if not success:
        raise HTTPException(status_code=404, detail="Project không tồn tại")
    return {"status": "ok"}

processing_stop_flag = False

class ProcessConfig(BaseModel):
    project_id: str
    pipeline_mode: str
    frame_interval: int
    bib_min: int
    bib_max: int

def _process_video_batch(batch_frames, batch_frame_counts, batch_timestamps, tracker, result_queue, config, fpath, do_face, do_bib, FaceProcessor, OCRProcessor, SentenceTransformer, process_interval, no_face_streak, thumb_dir):
    batch_faces = []
    if do_face and FaceProcessor:
        try:
            batch_faces = FaceProcessor.get_embeddings_batch(batch_frames)
        except Exception:
            batch_faces = [[] for _ in batch_frames]
    else:
        batch_faces = [[] for _ in batch_frames]

    for i in range(len(batch_frames)):
        b_frame = batch_frames[i]
        b_fcount = batch_frame_counts[i]
        b_ts = batch_timestamps[i]
        b_faces = batch_faces[i]

        if b_faces:
            process_interval = max(config.frame_interval // 2, 5)
            no_face_streak = 0
        else:
            no_face_streak += 1
            if no_face_streak >= 3:
                process_interval = min(config.frame_interval * 2, 90)

        if tracker:
            finished = tracker.update(b_faces, b_fcount, b_ts)
            if finished:
                thumb_path = os.path.join(thumb_dir, f"face_{uuid.uuid4().hex[:8]}.jpg")
                try:
                    preview = cv2.resize(b_frame, (320, int(b_frame.shape[0] * 320 / b_frame.shape[1])))
                    cv2.imwrite(thumb_path, preview)
                except:
                    thumb_path = None
                    
                vectors = np.array([t["best_face"]["embedding"] for t in finished])
                metadata = [{"source_path": fpath, "image_type": "video", "timestamp": t["start_timestamp"], "end_timestamp": t["end_timestamp"], "frame_idx": t["last_seen_frame_idx"], "bbox": t["best_face"]["bbox"], "det_score": t["best_face"]["det_score"], "type": "face", "track_id": t["id"], "thumbnail_path": thumb_path} for t in finished]
                result_queue.put({"type": "face", "vectors": vectors, "metadata": metadata})

        if do_bib and OCRProcessor and SentenceTransformer and b_faces:
            fh_f, fw_f = b_frame.shape[:2]
            for face in b_faces:
                fx1, fy1, fx2, fy2 = [int(v) for v in face["bbox"]]
                fw, fh = fx2-fx1, fy2-fy1
                cx1, cx2 = max(0, int(fx1-fw*.5)), min(fw_f, int(fx2+fw*.5))
                cy1, cy2 = min(fh_f, fy2), min(fh_f, int(fy2+fh*3))
                if cx2 <= cx1 or cy2 <= cy1: continue

                crop = b_frame[cy1:cy2, cx1:cx2]
                scale = 1.0
                if (cx2-cx1) > 320:
                    scale = 320/(cx2-cx1)
                    crop = cv2.resize(crop, (320, int((cy2-cy1)*scale)))
                try:
                    texts = OCRProcessor.get_text(crop)
                    if texts:
                        bibs = [t for t in texts if any(c.isdigit() for c in t["text"]) and config.bib_min <= len(t["text"].strip()) <= config.bib_max]
                        if bibs:
                            thumb_path = os.path.join(thumb_dir, f"bib_{uuid.uuid4().hex[:8]}.jpg")
                            try:
                                preview = cv2.resize(b_frame, (320, int(b_frame.shape[0] * 320 / b_frame.shape[1])))
                                cv2.imwrite(thumb_path, preview)
                            except:
                                thumb_path = None
                                
                            vectors = np.array([SentenceTransformer.encode([t["text"]])[0] for t in bibs])
                            metadata = [{"source_path": fpath, "image_type": "video", "timestamp": b_ts, "frame_idx": b_fcount, "text": t["text"], "score": t["score"], "type": "bib", "thumbnail_path": thumb_path} for t in bibs]
                            result_queue.put({"type": "bib", "vectors": vectors, "metadata": metadata})
                except Exception:
                    pass

    return process_interval, no_face_streak

async def run_processing(config: ProcessConfig):
    global processing_stop_flag, FaceProcessor, OCRProcessor, SentenceTransformer, model_status
    processing_stop_flag = False

    if model_status == "loading":
        await emit_log("⏳ AI Models đang được tải. Vui lòng chờ thông báo trên Banner góc trên màn hình.")
        await emit_stage("error")
        return
    elif model_status == "error":
        await emit_log("❌ Khởi tạo AI Models thất bại. Vui lòng khởi động lại app.")
        await emit_stage("error")
        return

    project = pm.get_project(config.project_id)
    if not project:
        await emit_log("Project không tồn tại.")
        return

    source_dir = project.get("source_dir")

    await emit_stage("init")
    await emit_log("Chuẩn bị AI Engine...")

    do_face = config.pipeline_mode in ("face_only", "face_bib")
    do_bib = config.pipeline_mode in ("bib_only", "face_bib")

    try:
        await emit_stage("ready")

        src = Path(source_dir)
        img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        vid_exts = {".mp4", ".avi", ".mov", ".mkv"}
        images = sorted(f for f in src.rglob("*") if f.suffix.lower() in img_exts)
        videos = sorted(f for f in src.rglob("*") if f.suffix.lower() in vid_exts)

        all_files = [(str(p), "image") for p in images] + [(str(p), "video") for p in videos]
        total = len(all_files)

        await emit_log(f"Đã tìm thấy: {len(images)} Ảnh, {len(videos)} Video")
        if total == 0:
            await emit_log("Thư mục trống.")
            await emit_stage("done")
            return

        pm.apply_index_paths(config.project_id)
        vs = VectorStore(load_existing=True)
        BATCH_SIZE = 4

        for idx, (fpath, ftype) in enumerate(all_files):
            if processing_stop_flag:
                await emit_log("🛑 Đã dừng theo yêu cầu.")
                break

            fname = os.path.basename(fpath)
            await emit_log(f"Đang xử lý: {fname}")

            if ftype == "image":
                img = cv2.imread(fpath)
                if img is not None:
                    if do_face and FaceProcessor:
                        faces = FaceProcessor.get_embedding(img)
                        if faces:
                            vs.add_vectors(
                                np.array([f["embedding"] for f in faces]),
                                [{"source_path": fpath, "image_type": "image", "bbox": f["bbox"], "det_score": f["det_score"], "type": "face"} for f in faces]
                            )
                    if do_bib and OCRProcessor and SentenceTransformer:
                        texts = OCRProcessor.get_text(img)
                        if texts:
                            bibs = [t for t in texts if any(c.isdigit() for c in t["text"]) and config.bib_min <= len(t["text"].strip()) <= config.bib_max]
                            if bibs:
                                vs.add_bib_vectors(
                                    np.array([SentenceTransformer.encode([t["text"]])[0] for t in bibs]),
                                    [{"source_path": fpath, "image_type": "image", "timestamp": 0, "frame_idx": 0, "text": t["text"], "score": t["score"], "type": "bib"} for t in bibs]
                                )
                vs.save()
            else:
                thumb_dir = os.path.join(source_dir, ".thumbnails")
                os.makedirs(thumb_dir, exist_ok=True)
                
                frame_queue = queue.Queue(maxsize=30)
                result_queue = queue.Queue()
                stop_event = threading.Event()
                
                def read_worker():
                    cap = cv2.VideoCapture(fpath)
                    if not cap.isOpened():
                        frame_queue.put(None)
                        return
                    fps = cap.get(cv2.CAP_PROP_FPS) or 30
                    frame_count = 0
                    prev_gray = None
                    
                    while not stop_event.is_set() and not processing_stop_flag:
                        ret, frame = cap.read()
                        if not ret: break
                        frame_count += 1
                        
                        try:
                            small = cv2.resize(frame, (160, 120))
                            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                            if prev_gray is not None:
                                diff = np.mean(cv2.absdiff(gray, prev_gray))
                                if diff < 1.5:
                                    continue
                            prev_gray = gray
                        except:
                            pass
                            
                        frame_queue.put((frame, frame_count, frame_count / fps))
                        
                    cap.release()
                    frame_queue.put(None)

                def detect_worker():
                    from app.core.tracker import FaceTracker
                    tracker = FaceTracker() if do_face else None
                    batch_frames, batch_frame_counts, batch_timestamps = [], [], []
                    process_interval = config.frame_interval
                    no_face_streak = 0
                    next_process_frame = 0
                    
                    while not stop_event.is_set() and not processing_stop_flag:
                        item = frame_queue.get()
                        if item is None:
                            if len(batch_frames) > 0:
                                process_interval, no_face_streak = _process_video_batch(
                                    batch_frames, batch_frame_counts, batch_timestamps,
                                    tracker, result_queue, config, fpath, do_face, do_bib,
                                    FaceProcessor, OCRProcessor, SentenceTransformer,
                                    process_interval, no_face_streak, thumb_dir
                                )
                            if tracker and do_face and FaceProcessor:
                                remaining = tracker.finalize()
                                if remaining:
                                    vectors = np.array([t["best_face"]["embedding"] for t in remaining])
                                    metadata = [{"source_path": fpath, "image_type": "video", "timestamp": t["start_timestamp"], "end_timestamp": t["end_timestamp"], "frame_idx": t["last_seen_frame_idx"], "bbox": t["best_face"]["bbox"], "det_score": t["best_face"]["det_score"], "type": "face", "track_id": t["id"], "thumbnail_path": None} for t in remaining]
                                    result_queue.put({"type": "face", "vectors": vectors, "metadata": metadata})
                            result_queue.put(None)
                            break
                            
                        frame, fcount, ts = item
                        if fcount < next_process_frame: continue
                        
                        next_process_frame = fcount + process_interval
                        batch_frames.append(frame)
                        batch_frame_counts.append(fcount)
                        batch_timestamps.append(ts)
                        
                        if len(batch_frames) >= BATCH_SIZE:
                            process_interval, no_face_streak = _process_video_batch(
                                batch_frames, batch_frame_counts, batch_timestamps,
                                tracker, result_queue, config, fpath, do_face, do_bib,
                                FaceProcessor, OCRProcessor, SentenceTransformer,
                                process_interval, no_face_streak, thumb_dir
                            )
                            batch_frames.clear(); batch_frame_counts.clear(); batch_timestamps.clear()

                def save_worker():
                    while not stop_event.is_set() and not processing_stop_flag:
                        item = result_queue.get()
                        if item is None: break
                        
                        if item["type"] == "face":
                            vs.add_vectors(item["vectors"], item["metadata"])
                        elif item["type"] == "bib":
                            vs.add_bib_vectors(item["vectors"], item["metadata"])

                t_read = threading.Thread(target=read_worker)
                t_detect = threading.Thread(target=detect_worker)
                t_save = threading.Thread(target=save_worker)
                
                t_read.start(); t_detect.start(); t_save.start()

                while t_read.is_alive() or t_detect.is_alive() or t_save.is_alive():
                    if processing_stop_flag: stop_event.set()
                    await asyncio.sleep(0.1)
                    
                t_read.join(); t_detect.join(); t_save.join()
                vs.save()

            await emit_progress(idx + 1, total)

        await emit_log("Hoàn tất toàn bộ files!")
        await emit_stage("done")
    except Exception as e:
        await emit_log(f"LỖI: {str(e)}")
        await emit_stage("error")

@app.post("/process/start")
async def start_process(config: ProcessConfig):
    global processing_stop_flag
    if not processing_stop_flag and hasattr(app, "processing_task") and not app.processing_task.done():
        raise HTTPException(status_code=400, detail="Đang có tiến trình xử lý chạy.")

    app.processing_task = asyncio.create_task(run_processing(config))
    return {"status": "started"}

@app.post("/process/stop")
async def stop_process():
    global processing_stop_flag
    processing_stop_flag = True
    return {"status": "stopping"}

@app.post("/search")
async def search(
    project_id: str = Form(...),
    type: str = Form("face"),
    k: int = Form(50),
    file: UploadFile = File(None),
    text: Optional[str] = Form(None),
    threshold: float = Form(0.4)
):
    global model_status, FaceProcessor, SentenceTransformer

    if model_status == "loading":
        raise HTTPException(status_code=400, detail="AI Models đang được tải. Vui lòng chờ banner trên cùng báo hoàn tất.")
    elif model_status == "error":
        raise HTTPException(status_code=500, detail="Lỗi AI Models. Vui lòng khởi động lại ứng dụng.")

    pm.apply_index_paths(project_id)
    vs = VectorStore(load_existing=True)
    results = []

    if type == "face":
        if not file:
            raise HTTPException(status_code=400, detail="Cần file ảnh để tìm theo khuôn mặt")

        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        faces = FaceProcessor.get_embedding(img)
        if not faces:
            raise HTTPException(status_code=400, detail="Không phát hiện khuôn mặt trong ảnh mẫu")

        target_face = max(faces, key=lambda x: x['det_score'])
        embedding = np.array([target_face['embedding']], dtype=np.float32)

        raw_results = vs.search(embedding, k=k*2)
        unique_videos = {}
        for res in raw_results:
            vid = res.get('source_path', res.get('video_path'))
            if res.get('score', 0) >= threshold:
                if vid not in unique_videos or res['score'] > unique_videos[vid]['score']:
                    unique_videos[vid] = res

        results = list(unique_videos.values())
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:k]

    elif type == "bib":
        if not text:
            raise HTTPException(status_code=400, detail="Cần mã BIB để tìm kiếm")

        embedding = SentenceTransformer.encode([text])
        raw_results = vs.search_bib(np.array(embedding, dtype=np.float32), k=k*2)

        unique_videos = {}
        for res in raw_results:
            vid = res.get('source_path', res.get('video_path'))
            if vid not in unique_videos or res['score'] > unique_videos[vid]['score']:
                unique_videos[vid] = res

        results = list(unique_videos.values())
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:k]

    return {"results": results}
