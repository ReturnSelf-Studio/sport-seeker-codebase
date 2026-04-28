"""
app/api/routers/engine.py
"""
import asyncio
import cv2
import numpy as np
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.core.project_manager import ProjectManager
from app.core.vector_store import VectorStore
from app.core.video_manifest import VideoManifest, backup_index, restore_index, clear_backup
from app.services.ai_engine import ai_engine
from app.services.video_pipeline import run_processing, ProcessConfig

router = APIRouter(tags=["Engine"])
pm = ProjectManager()

MAX_VIDEOS = 5000


# ── Pre-scan ──────────────────────────────────────────────────────────────────

@router.get("/process/prescan/{project_id}")
async def prescan(project_id: str):
    """
    Scan source_dir của project, trả về summary + danh sách video.
    Gọi trước khi user bấm Start để hiển thị review UI.
    """
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project không tồn tại")

    source_dir = project.get("source_dir", "")
    manifest = VideoManifest(project["project_dir"])

    # Reset mọi "scanning" còn sót từ session trước (crash recovery)
    manifest.reset_all_scanning()

    summary = manifest.sync_with_source(source_dir)
    videos = manifest.get_all_videos(source_dir)

    over_limit = summary["total"] > MAX_VIDEOS

    return {
        "summary": summary,
        "videos": videos,
        "over_limit": over_limit,
        "max_videos": MAX_VIDEOS,
    }


# ── Process control ───────────────────────────────────────────────────────────

@router.post("/process/start")
async def start_process(config: ProcessConfig):
    if not ai_engine.processing_stop_flag and ai_engine.current_task and not ai_engine.current_task.done():
        raise HTTPException(status_code=400, detail="Đang có tiến trình xử lý chạy.")

    project = pm.get_project(config.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project không tồn tại")

    # Backup index trước khi bắt đầu
    backup_index(project["project_dir"])

    ai_engine.processing_stop_flag = False
    ai_engine.processing_pause_flag = False
    ai_engine.current_config = config
    ai_engine.current_task = asyncio.create_task(run_processing(config))
    return {"status": "started"}


@router.post("/process/stop")
async def stop_process():
    ai_engine.processing_stop_flag = True
    ai_engine.processing_pause_flag = False
    return {"status": "stopping"}


@router.post("/process/cancel")
async def cancel_process():
    """
    Dừng task và rollback index về trạng thái trước session.
    Dùng khi user confirm hủy (ví dụ tắt app).
    """
    project_id = ai_engine.current_config.project_id if ai_engine.current_config else None

    # Dừng task
    ai_engine.processing_stop_flag = True
    ai_engine.processing_pause_flag = False

    # Chờ task dừng (tối đa 10s)
    if ai_engine.current_task and not ai_engine.current_task.done():
        try:
            await asyncio.wait_for(asyncio.shield(ai_engine.current_task), timeout=10.0)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            ai_engine.current_task.cancel()

    # Rollback
    if project_id:
        project = pm.get_project(project_id)
        if project:
            restored = restore_index(project["project_dir"])
            # Reset manifest: các video "scanning" về "no-scan"
            manifest = VideoManifest(project["project_dir"])
            manifest.reset_all_scanning()
            return {"status": "cancelled", "rollback": "success" if restored else "failed"}

    return {"status": "cancelled", "rollback": "skipped"}


@router.get("/process/status")
async def get_process_status():
    """
    Trả về trạng thái thực của task. Frontend gọi khi resume để sync lại state.
    """
    is_running = (
        not ai_engine.processing_stop_flag
        and ai_engine.current_task is not None
        and not ai_engine.current_task.done()
    )
    return {
        "is_running": is_running,
        "config": ai_engine.current_config.dict() if ai_engine.current_config else None,
    }


# ── Search ────────────────────────────────────────────────────────────────────

@router.post("/search")
async def search(
    project_id: str = Form(...),
    type: str = Form("face"),
    k: int = Form(50),
    file: UploadFile = File(None),
    text: Optional[str] = Form(None),
    threshold: float = Form(0.4)
):
    if ai_engine.model_status == "loading":
        raise HTTPException(status_code=400, detail="AI Models đang được tải. Vui lòng chờ banner trên cùng báo hoàn tất.")
    elif ai_engine.model_status == "error":
        raise HTTPException(status_code=500, detail="Lỗi AI Models. Vui lòng khởi động lại ứng dụng.")

    # Chặn search khi đang xử lý
    if (
        not ai_engine.processing_stop_flag
        and ai_engine.current_task is not None
        and not ai_engine.current_task.done()
    ):
        raise HTTPException(status_code=400, detail="Vui lòng chờ quét xong trước khi tìm kiếm.")

    pm.apply_index_paths(project_id)
    vs = VectorStore(load_existing=True)
    results = []

    if type == "face":
        if not file:
            raise HTTPException(status_code=400, detail="Cần file ảnh để tìm theo khuôn mặt")

        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        faces = ai_engine.FaceProcessor.get_embedding(img)
        if not faces:
            return {"results": []}

        target_face = max(faces, key=lambda x: x['det_score'])
        embedding = np.array([target_face['embedding']], dtype=np.float32)

        raw_results = vs.search(embedding, k=k * 2)
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

        embedding = ai_engine.SentenceTransformer.encode([text])
        raw_results = vs.search_bib(np.array(embedding, dtype=np.float32), k=k * 2)

        unique_videos = {}
        for res in raw_results:
            vid = res.get('source_path', res.get('video_path'))
            if vid not in unique_videos or res['score'] > unique_videos[vid]['score']:
                unique_videos[vid] = res

        results = list(unique_videos.values())
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:k]

    return {"results": results}
