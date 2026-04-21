import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from app.core.config import settings

# Tăng giới hạn đệ quy an toàn
sys.setrecursionlimit(50000)
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

from sentence_transformers import SentenceTransformer as ST
from app.core.face_processor import FaceProcessor as FP
from app.core.ocr_processor import OCRProcessor as OP

class AIEngine:
    def __init__(self):
        self.FaceProcessor = None
        self.OCRProcessor = None
        self.SentenceTransformer = None
        self.model_status = "loading"
        self.model_loading_message = "Đang chuẩn bị khởi tạo..."
        
        # Thêm cờ quản lý luồng
        self.processing_stop_flag = False
        self.processing_pause_flag = False
        self.current_config = None
        self.current_task = None

    def write_checkpoint(self, msg):
        cp_file = None
        try:
            if sys.platform == 'win32':
                log_dir = Path(os.environ.get('APPDATA', '')) / "SportSeeker" / "logs"
            else:
                log_dir = Path.home() / "SportSeeker" / "logs"
            
            log_dir.mkdir(parents=True, exist_ok=True)
            cp_file = log_dir / "checkpoints.log"
            
            with open(cp_file, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
                f.flush()
        except Exception as e:
            if cp_file is not None:
                try:
                    with open(cp_file, "a", encoding="utf-8") as f:
                        f.write(f"CHECKPOINT_ERROR: {str(e)}\n")
                        f.flush()
                except:
                    pass
            print(f"Lỗi khi ghi checkpoint: {str(e)}", flush=True)

    def background_model_loader(self):
        try:
            self.write_checkpoint("▶ BẮT ĐẦU KHỞI TẠO HỆ THỐNG AI")
            
            self.write_checkpoint("⏳ [1/3] Đang nạp Text Embedding...")
            self.SentenceTransformer = ST(settings.TEXT_EMBEDDING_MODEL)
            sys.stderr.write("30%|\n")
            self.write_checkpoint("✅ XONG Text Embedding.")

            self.write_checkpoint("⏳ [2/3] Đang nạp InsightFace (Khuôn mặt)...")
            self.FaceProcessor = FP()
            sys.stderr.write("65%|\n")
            self.write_checkpoint("✅ XONG InsightFace.")

            self.write_checkpoint("⏳ [3/3] Đang nạp PaddleOCR (Số BIB)...")
            self.OCRProcessor = OP()
            sys.stderr.write("100%|\n")
            self.write_checkpoint("✅ XONG PaddleOCR.")

            self.model_status = "ready"
            self.model_loading_message = "Khởi tạo AI Models thành công!"
            self.write_checkpoint("🎉 TẤT CẢ MÔ HÌNH ĐÃ SẴN SÀNG!")
            
        except Exception as e:
            error_msg = f"❌ LỖI CHÍ MẠNG: {str(e)}"
            self.write_checkpoint(error_msg)
            self.model_status = "error"
            self.model_loading_message = error_msg

    def start_loading(self):
        try:
            threading.stack_size(67108864)
        except Exception:
            pass
        threading.Thread(target=self.background_model_loader, daemon=True).start()

ai_engine = AIEngine()
