import os
import time
import threading
from pathlib import Path
from fastapi import APIRouter

from app.services.ai_engine import ai_engine

router = APIRouter(tags=["System"])

@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "Backend is healthy"}

@router.get("/models/status")
def get_model_status():
    return {"status": ai_engine.model_status, "message": ai_engine.model_loading_message}

@router.get("/system/storage")
def get_system_storage():
    """Lấy dung lượng Cache thư mục AI"""
    def get_size(path):
        total = 0
        if os.path.exists(path):
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        try:
                            total += os.path.getsize(fp)
                        except Exception:
                            pass
        return total

    home = str(Path.home())
    ocr_size = get_size(os.path.join(home, ".paddleocr"))
    ocr_size += get_size(os.path.join(home, ".paddlex"))
    ocr_size += get_size(os.path.join(home, ".paddle"))
    
    return {
        "paddleocr_mb": round(ocr_size / (1024 * 1024), 2)
    }

@router.post("/shutdown")
async def shutdown_server():
    def kill_me():
        time.sleep(0.5)
        os._exit(0)
    threading.Thread(target=kill_me, daemon=True).start()
    return {"status": "ok", "message": "Shutting down..."}
