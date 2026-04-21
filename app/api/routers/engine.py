import asyncio
import cv2
import numpy as np
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.core.project_manager import ProjectManager
from app.core.vector_store import VectorStore
from app.services.ai_engine import ai_engine
from app.services.video_pipeline import run_processing, ProcessConfig

router = APIRouter(tags=["Engine"])
pm = ProjectManager()

@router.post("/process/start")
async def start_process(config: ProcessConfig):
    if not ai_engine.processing_stop_flag and ai_engine.current_task and not ai_engine.current_task.done():
        raise HTTPException(status_code=400, detail="Đang có tiến trình xử lý chạy.")

    ai_engine.current_config = config
    ai_engine.current_task = asyncio.create_task(run_processing(config))
    return {"status": "started"}

@router.post("/process/stop")
async def stop_process():
    ai_engine.processing_stop_flag = True
    ai_engine.processing_pause_flag = False # Đảm bảo thoát khỏi loop pause
    return {"status": "stopping"}

# API MỚI CHO TICKET 23
@router.post("/process/pause")
async def pause_process():
    ai_engine.processing_pause_flag = True
    return {"status": "paused"}

@router.post("/process/resume")
async def resume_process():
    ai_engine.processing_pause_flag = False
    return {"status": "resumed"}

@router.post("/process/update_config")
async def update_process_config(config: ProcessConfig):
    ai_engine.current_config = config
    return {"status": "config_updated"}

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
        # FIX TICKET 22: Trả về rỗng thay vì Exception khi ảnh không có mặt
        if not faces:
            return {"results": []}

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

        embedding = ai_engine.SentenceTransformer.encode([text])
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
