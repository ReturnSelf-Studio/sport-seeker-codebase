"""
main.py — Sport Seeker Backend Entry Point.
"""
import os
import sys

# PHẢI ĐẶT TRƯỚC MỌI IMPORT — Paddle runtime đọc flags lúc load DLL.
if sys.platform == 'win32':
    os.environ["FLAGS_use_mkldnn"] = "0"
    os.environ["FLAGS_use_new_executor"] = "0"
    os.environ["PADDLE_DISABLE_ONEDNN"] = "1"

print("\n" + "="*60, flush=True)
print(f"🕵️ KIỂM TRA MÔI TRƯỜNG KHỞI CHẠY", flush=True)
print(f" -> PID: {os.getpid()}", flush=True)
print(f" -> CWD (Thư mục làm việc): {os.getcwd()}", flush=True)
print(f" -> Executable (File chạy): {sys.executable}", flush=True)
print(f" -> Prefix (Môi trường ảo): {sys.prefix}", flush=True)

try:
    import posthog
    print(f" -> ✅ POSTHOG OK! File thư viện nằm tại: {posthog.__file__}", flush=True)
except ImportError as e:
    print(f" -> ❌ LỖI POSTHOG: Không tìm thấy thư viện. ({e})", flush=True)
print("="*60 + "\n", flush=True)

import multiprocessing
from pathlib import Path

# Tăng giới hạn đệ quy để tránh crash PaddleOCR/PaddlePaddle
sys.setrecursionlimit(100000)

# Cấu hình nạp DLL cho Windows khi đóng gói exe
if sys.platform == 'win32' and getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    for extra_path in [base_path, os.path.join(base_path, 'faiss'), os.path.join(base_path, 'numpy.libs')]:
        if os.path.exists(extra_path):
            os.add_dll_directory(extra_path)
            os.environ['PATH'] = extra_path + os.pathsep + os.environ['PATH']

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "TRUE")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# --- SETUP LOGGING TỪ MODULE CORE ---
from app.core.logger import setup_logging
setup_logging()

import uvicorn
import app.api.server

def main():
    multiprocessing.freeze_support()
    print("[SportSeeker] Starting Backend API on 127.0.0.1:10330...")
    uvicorn.run("app.api.server:app", host="127.0.0.1", port=10330, reload=False)

if __name__ == "__main__":
    main()
