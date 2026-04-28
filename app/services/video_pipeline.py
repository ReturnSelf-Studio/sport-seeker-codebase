"""
app/services/video_pipeline.py

Pipeline xử lý video/ảnh với:
- VideoManifest tracking: skip video đã done, mark scanning/done/failed
- Incremental save: vs.save() sau mỗi video
- Stop giữa video: video đang dở không được mark done
- Backup/restore tích hợp qua engine.py
"""

import json
import os
import time
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
from app.core.video_manifest import VideoManifest, clear_backup
from app.services.ai_engine import ai_engine
from app.services.ws_manager import emit_log, emit_stage, ws_manager

pm = ProjectManager()


class ProcessConfig(BaseModel):
    project_id: str
    pipeline_mode: str
    frame_interval: int
    bib_min: int
    bib_max: int
    rescan_all: bool = False  # True = quét lại cả video đã done


def imwrite_unicode(path, img):
    try:
        is_success, im_buf_arr = cv2.imencode(".jpg", img)
        if is_success:
            im_buf_arr.tofile(path)
            return True
        return False
    except Exception:
        return False


def imread_unicode(path):
    try:
        img_arr = np.fromfile(path, np.uint8)
        return cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
    except Exception:
        return None


def _process_video_batch(batch_frames, batch_frame_counts, batch_timestamps, tracker,
                         result_queue, config, fpath, do_face, do_bib,
                         FaceProcessor, OCRProcessor, SentenceTransformer,
                         process_interval, no_face_streak, thumb_dir):
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
                metadata = [{"source_path": fpath, "image_type": "video",
                             "timestamp": float(t["start_timestamp"]),
                             "end_timestamp": float(t["end_timestamp"]),
                             "frame_idx": int(t["last_seen_frame_idx"]),
                             "bbox": t["best_face"]["bbox"],
                             "det_score": float(t["best_face"]["det_score"]),
                             "type": "face", "track_id": t["id"],
                             "thumbnail_path": thumb_path} for t in finished]
                result_queue.put({"type": "face", "vectors": vectors, "metadata": metadata})

        if do_bib and OCRProcessor and SentenceTransformer and b_faces:
            fh_f, fw_f = b_frame.shape[:2]
            for face in b_faces:
                fx1, fy1, fx2, fy2 = [int(v) for v in face["bbox"]]
                fw, fh = fx2 - fx1, fy2 - fy1
                cx1, cx2 = max(0, int(fx1 - fw * .5)), min(fw_f, int(fx2 + fw * .5))
                cy1, cy2 = min(fh_f, fy2), min(fh_f, int(fy2 + fh * 3))
                if cx2 <= cx1 or cy2 <= cy1:
                    continue

                crop = b_frame[cy1:cy2, cx1:cx2]
                ch, cw = crop.shape[:2]
                if ch == 0 or cw == 0:
                    continue

                scale = 320.0 / cw
                resized_h = max(1, int(ch * scale))
                crop_resized = cv2.resize(crop, (320, resized_h))
                if resized_h < 320:
                    crop_resized = cv2.copyMakeBorder(
                        crop_resized, 0, 320 - resized_h, 0, 0,
                        cv2.BORDER_CONSTANT, value=(0, 0, 0))

                try:
                    texts = OCRProcessor.get_text(crop_resized)
                    if texts:
                        bibs = [t for t in texts if any(c.isdigit() for c in t["text"])
                                and config.bib_min <= len(t["text"].strip()) <= config.bib_max]
                        if bibs:
                            thumb_path = os.path.join(thumb_dir, f"bib_{uuid.uuid4().hex[:8]}.jpg")
                            try:
                                preview = cv2.resize(b_frame, (320, int(b_frame.shape[0] * 320 / b_frame.shape[1])))
                                if not imwrite_unicode(thumb_path, preview):
                                    thumb_path = None
                            except Exception:
                                thumb_path = None

                            vectors = np.array(
                                [SentenceTransformer.encode([t["text"]])[0] for t in bibs], dtype=np.float32)
                            metadata = [{"source_path": fpath, "image_type": "video",
                                         "timestamp": float(b_ts), "frame_idx": int(b_fcount),
                                         "text": t["text"], "score": float(t["score"]),
                                         "type": "bib", "thumbnail_path": thumb_path} for t in bibs]
                            result_queue.put({"type": "bib", "vectors": vectors, "metadata": metadata})
                except Exception as e:
                    print(f"[CẢNH BÁO] Lỗi OCR/BIB: {e}", flush=True)

    return process_interval, no_face_streak


async def _process_single_video(fpath: str, vs: VectorStore, manifest: VideoManifest,
                                config, do_face: bool, do_bib: bool) -> bool:
    """
    Xử lý 1 video. Returns True nếu hoàn tất, False nếu bị interrupt.
    vs.save() được gọi sau khi video hoàn tất thành công.
    """
    from app.core.tracker import FaceTracker

    fname = os.path.basename(fpath)
    project = pm.get_project(config.project_id)
    thumb_dir = os.path.join(project["project_dir"], ".thumbnails")
    os.makedirs(thumb_dir, exist_ok=True)

    manifest.mark_scanning(fname)

    cap = cv2.VideoCapture(fpath)
    if not cap.isOpened():
        await emit_log(f"   ⚠ Không mở được video: {fname}")
        manifest.mark_failed(fname)
        return False

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    duration = total_frames / fps if total_frames > 0 else None
    cap.release()

    frame_queue: queue.Queue = queue.Queue(maxsize=32)
    result_queue: queue.Queue = queue.Queue()
    stop_event = threading.Event()
    video_stats = {"processed": 0, "total": total_frames}
    BATCH_SIZE = 4

    tracker = FaceTracker() if do_face else None

    def read_worker():
        cap_inner = cv2.VideoCapture(fpath)
        fcount = 0
        try:
            while not stop_event.is_set() and not ai_engine.processing_stop_flag:
                ret, frame = cap_inner.read()
                if not ret:
                    break
                frame_queue.put((frame, fcount, fcount / fps))
                fcount += 1
        finally:
            frame_queue.put(None)
            cap_inner.release()

    def detect_worker():
        process_interval = config.frame_interval
        next_process_frame = 0
        no_face_streak = 0
        batch_frames, batch_frame_counts, batch_timestamps = [], [], []

        while not stop_event.is_set() and not ai_engine.processing_stop_flag:
            try:
                item = frame_queue.get(timeout=2)
            except queue.Empty:
                continue

            if item is None:
                if batch_frames:
                    _process_video_batch(
                        batch_frames, batch_frame_counts, batch_timestamps,
                        tracker, result_queue, config, fpath, do_face, do_bib,
                        ai_engine.FaceProcessor, ai_engine.OCRProcessor, ai_engine.SentenceTransformer,
                        process_interval, no_face_streak, thumb_dir)
                if tracker:
                    remaining = tracker.finalize()
                    if remaining:
                        vectors = np.array([t["best_face"]["embedding"] for t in remaining])
                        metadata = [{"source_path": fpath, "image_type": "video",
                                     "timestamp": float(t["start_timestamp"]),
                                     "end_timestamp": float(t["end_timestamp"]),
                                     "frame_idx": int(t["last_seen_frame_idx"]),
                                     "bbox": t["best_face"]["bbox"],
                                     "det_score": float(t["best_face"]["det_score"]),
                                     "type": "face", "track_id": t["id"],
                                     "thumbnail_path": None} for t in remaining]
                        result_queue.put({"type": "face", "vectors": vectors, "metadata": metadata})
                result_queue.put(None)
                break

            frame, fcount, ts = item
            video_stats["processed"] = fcount

            if fcount < next_process_frame:
                continue

            next_process_frame = fcount + process_interval
            batch_frames.append(frame)
            batch_frame_counts.append(fcount)
            batch_timestamps.append(ts)

            if len(batch_frames) >= BATCH_SIZE:
                dyn_conf = ai_engine.current_config or config
                process_interval, no_face_streak = _process_video_batch(
                    batch_frames, batch_frame_counts, batch_timestamps,
                    tracker, result_queue, dyn_conf, fpath, do_face, do_bib,
                    ai_engine.FaceProcessor, ai_engine.OCRProcessor, ai_engine.SentenceTransformer,
                    process_interval, no_face_streak, thumb_dir)
                batch_frames.clear()
                batch_frame_counts.clear()
                batch_timestamps.clear()

    def save_worker():
        while not stop_event.is_set() and not ai_engine.processing_stop_flag:
            try:
                item = result_queue.get(timeout=1)
                if item is None:
                    break
                if item["type"] == "face":
                    vs.add_vectors(item["vectors"], item["metadata"])
                elif item["type"] == "bib":
                    vs.add_bib_vectors(item["vectors"], item["metadata"])
            except queue.Empty:
                pass
            except Exception as e:
                print(f"[CẢNH BÁO] Lỗi save vector: {e}", flush=True)

    t_read = threading.Thread(target=read_worker, daemon=True)
    t_detect = threading.Thread(target=detect_worker, daemon=True)
    t_save = threading.Thread(target=save_worker, daemon=True)
    t_read.start()
    t_detect.start()
    t_save.start()

    last_log_time = time.time()
    while t_read.is_alive() or t_detect.is_alive() or t_save.is_alive():
        if ai_engine.processing_stop_flag:
            stop_event.set()

        now = time.time()
        if now - last_log_time >= 2.0:
            cf = video_stats["processed"]
            tf = video_stats["total"]
            if tf > 0 and cf > 0:
                pct = min((cf / tf) * 100, 100.0)
                await emit_log(f"   ▶ {fname}: {cf}/{tf} frames ({pct:.1f}%)")
            last_log_time = now

        await asyncio.sleep(0.1)

    t_read.join()
    t_detect.join()
    t_save.join()

    if ai_engine.processing_stop_flag:
        manifest.mark_failed(fname)
        return False

    vs.save()
    manifest.mark_done(fname, duration_seconds=duration)
    await emit_log(f"   ✅ Xong: {fname}")
    await ws_manager.broadcast(json.dumps({
        "type": "video_done",
        "data": {"name": fname, "total_frames": total_frames}
    }))
    return True


async def run_processing(config: ProcessConfig):
    ai_engine.processing_stop_flag = False
    ai_engine.processing_pause_flag = False

    if ai_engine.model_status == "loading":
        await emit_log("⏳ AI Models đang được tải.")
        await emit_stage("error")
        return
    elif ai_engine.model_status == "error":
        await emit_log("❌ Khởi tạo AI Models thất bại.")
        await emit_stage("error")
        return

    project = pm.get_project(config.project_id)
    if not project:
        await emit_log("Project không tồn tại.")
        await emit_stage("error")
        return

    source_dir = project.get("source_dir")
    manifest = VideoManifest(project["project_dir"])

    await emit_stage("init")
    await emit_log("Chuẩn bị AI Engine...")

    do_face = config.pipeline_mode in ("face_only", "face_bib")
    do_bib = config.pipeline_mode in ("bib_only", "face_bib")

    try:
        await emit_stage("ready")

        src = Path(source_dir)
        img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

        images = sorted(
            (f for f in src.rglob("*")
             if f.suffix.lower() in img_exts
             and ".thumbnails" not in f.parts
             and ".ss_meta" not in f.parts),
            key=lambda f: f.stat().st_size if f.exists() else 0
        )

        if config.rescan_all:
            raw_videos = [
                f for f in src.rglob("*")
                if f.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}
                and ".ss_meta" not in f.parts
            ]
        else:
            raw_videos = [Path(p) for p in manifest.get_pending_videos(source_dir)]

        video_paths = sorted(
            (str(f) for f in raw_videos),
            key=lambda p: Path(p).stat().st_size if Path(p).exists() else 0
        )

        all_files = [(str(p), "image") for p in images] + [(v, "video") for v in video_paths]
        total = len(all_files)

        await emit_log(f"Tìm thấy: {len(images)} ảnh, {len(video_paths)} video cần quét")

        if total == 0:
            await emit_log("Không có file nào cần xử lý.")
            await emit_stage("done")
            clear_backup(project["project_dir"])
            return

        pm.apply_index_paths(config.project_id)
        vs = VectorStore(load_existing=True)

        for idx, (fpath, ftype) in enumerate(all_files):
            while ai_engine.processing_pause_flag and not ai_engine.processing_stop_flag:
                await asyncio.sleep(0.5)

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
                            vectors = np.array([f["embedding"] for f in faces])
                            metadata = [{"source_path": fpath, "image_type": "image",
                                         "type": "face", "det_score": float(f["det_score"]),
                                         "bbox": f["bbox"]} for f in faces]
                            vs.add_vectors(vectors, metadata)

                    if do_bib and ai_engine.OCRProcessor and ai_engine.SentenceTransformer:
                        texts = ai_engine.OCRProcessor.get_text(img)
                        if texts:
                            bibs = [t for t in texts if any(c.isdigit() for c in t["text"])
                                    and config.bib_min <= len(t["text"].strip()) <= config.bib_max]
                            if bibs:
                                vectors = np.array(
                                    [ai_engine.SentenceTransformer.encode([t["text"]])[0] for t in bibs],
                                    dtype=np.float32)
                                metadata = [{"source_path": fpath, "image_type": "image",
                                             "text": t["text"], "score": float(t["score"]),
                                             "type": "bib"} for t in bibs]
                                vs.add_bib_vectors(vectors, metadata)

                vs.save()

            elif ftype == "video":
                completed = await _process_single_video(
                    fpath, vs, manifest, config, do_face, do_bib)
                if not completed and ai_engine.processing_stop_flag:
                    break

        if not ai_engine.processing_stop_flag:
            await emit_log("✅ Hoàn tất toàn bộ!")
            await emit_stage("done")
            clear_backup(project["project_dir"])
        else:
            await emit_stage("stopped")

    except Exception as e:
        await emit_log(f"LỖI: {str(e)}")
        await emit_stage("error")
