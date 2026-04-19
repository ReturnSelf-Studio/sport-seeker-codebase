import os
import asyncio
import threading
import queue
import uuid
import cv2
import numpy as np
from pathlib import Path
from pydantic import BaseModel

from app.core.project_manager import ProjectManager
from app.core.vector_store import VectorStore
from app.services.ai_engine import ai_engine
from app.services.ws_manager import emit_log, emit_progress, emit_stage

pm = ProjectManager()

class ProcessConfig(BaseModel):
    project_id: str
    pipeline_mode: str
    frame_interval: int
    bib_min: int
    bib_max: int

# ==========================================
# HÀM HỖ TRỢ ĐỌC/GHI ẢNH UNICODE CHO WINDOWS
# ==========================================
def imwrite_unicode(path, img):
    """Ghi ảnh an toàn với đường dẫn tiếng Việt trên Windows"""
    try:
        is_success, im_buf_arr = cv2.imencode(".jpg", img)
        if is_success:
            im_buf_arr.tofile(path)
            return True
        return False
    except Exception:
        return False

def imread_unicode(path):
    """Đọc ảnh an toàn với đường dẫn tiếng Việt trên Windows"""
    try:
        img_arr = np.fromfile(path, np.uint8)
        return cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
    except Exception:
        return None
# ==========================================

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
                    if not imwrite_unicode(thumb_path, preview):
                        thumb_path = None
                except Exception:
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
                                if not imwrite_unicode(thumb_path, preview):
                                    thumb_path = None
                            except Exception:
                                thumb_path = None
                                
                            vectors = np.array([SentenceTransformer.encode([t["text"]])[0] for t in bibs])
                            metadata = [{"source_path": fpath, "image_type": "video", "timestamp": b_ts, "frame_idx": b_fcount, "text": t["text"], "score": t["score"], "type": "bib", "thumbnail_path": thumb_path} for t in bibs]
                            result_queue.put({"type": "bib", "vectors": vectors, "metadata": metadata})
                except Exception:
                    pass

    return process_interval, no_face_streak

async def run_processing(config: ProcessConfig):
    ai_engine.processing_stop_flag = False

    if ai_engine.model_status == "loading":
        await emit_log("⏳ AI Models đang được tải. Vui lòng chờ thông báo trên Banner góc trên màn hình.")
        await emit_stage("error")
        return
    elif ai_engine.model_status == "error":
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
        
        # ==========================================
        # FIX: Chủ động bỏ qua thư mục .thumbnails để tránh loop lặp vô hạn
        # Bằng cách check ".thumbnails" not in f.parts
        # ==========================================
        images = sorted(f for f in src.rglob("*") if f.suffix.lower() in img_exts and ".thumbnails" not in f.parts)
        videos = sorted(f for f in src.rglob("*") if f.suffix.lower() in vid_exts and ".thumbnails" not in f.parts)

        all_files = [(str(p), "image") for p in images] + [(str(p), "video") for p in videos]
        total = len(all_files)

        await emit_log(f"Đã tìm thấy: {len(images)} Ảnh, {len(videos)} Video (đã bỏ qua thumbnails cache)")
        if total == 0:
            await emit_log("Thư mục trống.")
            await emit_stage("done")
            return

        pm.apply_index_paths(config.project_id)
        vs = VectorStore(load_existing=True)
        BATCH_SIZE = 4

        for idx, (fpath, ftype) in enumerate(all_files):
            if ai_engine.processing_stop_flag:
                await emit_log("🛑 Đã dừng theo yêu cầu.")
                break

            fname = os.path.basename(fpath)
            await emit_log(f"Đang xử lý: {fname}")

            if ftype == "image":
                img = imread_unicode(fpath)
                if img is not None:
                    if do_face and ai_engine.FaceProcessor:
                        faces = ai_engine.FaceProcessor.get_embedding(img)
                        if faces:
                            vs.add_vectors(
                                np.array([f["embedding"] for f in faces]),
                                [{"source_path": fpath, "image_type": "image", "bbox": f["bbox"], "det_score": f["det_score"], "type": "face"} for f in faces]
                            )
                    if do_bib and ai_engine.OCRProcessor and ai_engine.SentenceTransformer:
                        texts = ai_engine.OCRProcessor.get_text(img)
                        if texts:
                            bibs = [t for t in texts if any(c.isdigit() for c in t["text"]) and config.bib_min <= len(t["text"].strip()) <= config.bib_max]
                            if bibs:
                                vs.add_bib_vectors(
                                    np.array([ai_engine.SentenceTransformer.encode([t["text"]])[0] for t in bibs]),
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
                    
                    while not stop_event.is_set() and not ai_engine.processing_stop_flag:
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
                    
                    while not stop_event.is_set() and not ai_engine.processing_stop_flag:
                        item = frame_queue.get()
                        if item is None:
                            if len(batch_frames) > 0:
                                process_interval, no_face_streak = _process_video_batch(
                                    batch_frames, batch_frame_counts, batch_timestamps,
                                    tracker, result_queue, config, fpath, do_face, do_bib,
                                    ai_engine.FaceProcessor, ai_engine.OCRProcessor, ai_engine.SentenceTransformer,
                                    process_interval, no_face_streak, thumb_dir
                                )
                            if tracker and do_face and ai_engine.FaceProcessor:
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
                                ai_engine.FaceProcessor, ai_engine.OCRProcessor, ai_engine.SentenceTransformer,
                                process_interval, no_face_streak, thumb_dir
                            )
                            batch_frames.clear(); batch_frame_counts.clear(); batch_timestamps.clear()

                def save_worker():
                    while not stop_event.is_set() and not ai_engine.processing_stop_flag:
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
                    if ai_engine.processing_stop_flag: stop_event.set()
                    await asyncio.sleep(0.1)
                    
                t_read.join(); t_detect.join(); t_save.join()
                vs.save()

            await emit_progress(idx + 1, total)

        await emit_log("Hoàn tất toàn bộ files!")
        await emit_stage("done")
    except Exception as e:
        await emit_log(f"LỖI: {str(e)}")
        await emit_stage("error")
