import os
import sys
import platform
import threading
import concurrent.futures
import importlib.metadata
from datetime import datetime
from pathlib import Path
from app.core.config import settings

# =====================================================================
# 1. BẢO HIỂM MAC OTA: Lừa thư viện imageio để vượt lỗi thiếu metadata
# =====================================================================
original_version = importlib.metadata.version

def patched_version(pkg_name):
    if pkg_name == "imageio":
        return "2.31.0"
    return original_version(pkg_name)

importlib.metadata.version = patched_version

# Tăng giới hạn đệ quy an toàn cho hệ thống
sys.setrecursionlimit(100000)
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

class AIEngine:
    def __init__(self):
        self.FaceProcessor = None
        self.OCRProcessor = None
        self.SentenceTransformer = None
        self.model_status = "loading"
        self.model_loading_message = "Đang chuẩn bị khởi tạo..."
        
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
            pass 

    # --- TÁCH HÀM LOAD MODEL RIÊNG BIỆT ĐỂ CHẠY ĐA LUỒNG ---
    def _load_text_embedding(self):
        sys.setrecursionlimit(100000)
        from sentence_transformers import SentenceTransformer as ST
        self.SentenceTransformer = ST(settings.TEXT_EMBEDDING_MODEL)

    def _load_insightface(self):
        sys.setrecursionlimit(100000)
        from app.core.face_processor import FaceProcessor as FP
        self.FaceProcessor = FP()

    def _load_paddleocr(self):
        sys.setrecursionlimit(100000)
        from app.core.ocr_processor import OCRProcessor as OP
        self.OCRProcessor = OP()

    def background_model_loader(self):
        import traceback
        try:
            self.write_checkpoint("▶ BẮT ĐẦU KHỞI TẠO HỆ THỐNG AI")
            
            # --- PHÂN LUỒNG XỬ LÝ THEO OS ---
            if sys.platform == "darwin":
                self.write_checkpoint("⏳ Hệ thống macOS: Nạp các model AI song song (Multi-threading)...")
                
                # Dùng ThreadPoolExecutor để chạy song song 3 tác vụ, cách ly stack
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    future_te = executor.submit(self._load_text_embedding)
                    future_if = executor.submit(self._load_insightface)
                    future_ocr = executor.submit(self._load_paddleocr)
                    
                    # Đợi kết quả và check lỗi từng model
                    for name, future in [("Text Embedding", future_te), ("InsightFace", future_if), ("PaddleOCR", future_ocr)]:
                        try:
                            future.result() # Will raise exception if occurred inside thread
                            self.write_checkpoint(f"✅ XONG {name}.")
                        except Exception as e:
                            self.write_checkpoint(f"❌ LỖI {name}: {str(e)}")
                            raise e 
            else:
                # Luồng Windows: Giữ nguyên chạy tuần tự do đang hoạt động ổn định
                self.write_checkpoint("⏳ [1/3] Đang nạp Text Embedding...")
                self._load_text_embedding()
                sys.__stderr__.write("30%|\n"); sys.__stderr__.flush()
                self.write_checkpoint("✅ XONG Text Embedding.")

                self.write_checkpoint("⏳ [2/3] Đang nạp InsightFace (Khuôn mặt)...")
                self._load_insightface()
                sys.__stderr__.write("65%|\n"); sys.__stderr__.flush()
                self.write_checkpoint("✅ XONG InsightFace.")

                self.write_checkpoint("⏳ [3/3] Đang nạp PaddleOCR (Số BIB)...")
                self._load_paddleocr()
                sys.__stderr__.write("100%|\n"); sys.__stderr__.flush()
                self.write_checkpoint("✅ XONG PaddleOCR.")

            self.model_status = "ready"
            self.model_loading_message = "Khởi tạo AI Models thành công!"
            self.write_checkpoint("🎉 TẤT CẢ MÔ HÌNH ĐÃ SẴN SÀNG!")
            
        except Exception as e:
            err_details = traceback.format_exc()
            error_msg = f"❌ LỖI CHÍ MẠNG: {str(e)}\n{err_details}"
            self.write_checkpoint(error_msg)
            self.model_status = "error"
            self.model_loading_message = f"❌ LỖI CHÍ MẠNG: {str(e)}"

    def start_loading(self):
        try:
            # Set stack size lớn (64MB) cho TẤT CẢ các luồng được tạo ra sau lệnh này
            threading.stack_size(67108864)
        except Exception:
            pass
        threading.Thread(target=self.background_model_loader, daemon=True).start()

ai_engine = AIEngine()
