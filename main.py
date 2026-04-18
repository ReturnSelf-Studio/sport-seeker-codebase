"""
main.py — Sport Seeker Backend Entry Point.
"""
import os
import sys
import multiprocessing
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Tăng giới hạn đệ quy để tránh crash PaddleOCR/PaddlePaddle
sys.setrecursionlimit(5000)

# Cấu hình nạp DLL cho Windows khi đóng gói
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

def setup_logging():
    if sys.platform == 'win32':
        log_dir = Path(os.environ.get('APPDATA', '')) / "SportSeeker" / "logs"
    else:
        log_dir = Path.home() / "SportSeeker" / "logs"
        
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "backend.log"

    # SET SIZE: 20MB per file, giữ 5 bản sao lưu
    handler = RotatingFileHandler(log_file, maxBytes=20*1024*1024, backupCount=5, encoding='utf-8')
    formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)

    logger = logging.getLogger("SportSeekerBackend")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    class StreamToLogger:
        def __init__(self, logger, original_stream, log_level):
            self.logger = logger
            self.original_stream = original_stream
            self.log_level = log_level

        def write(self, message):
            if message.strip():
                self.logger.log(self.log_level, message.strip())
            try:
                self.original_stream.write(message)
                self.original_stream.flush()
            except (UnicodeEncodeError, Exception):
                # Nếu console Windows không hỗ trợ tiếng Việt, in bản không dấu để tránh crash luồng
                try:
                    safe_msg = message.encode('ascii', errors='ignore').decode('ascii')
                    self.original_stream.write(safe_msg)
                    self.original_stream.flush()
                except:
                    pass

        def flush(self):
            self.original_stream.flush()

        def __getattr__(self, attr):
            return getattr(self.original_stream, attr)

    sys.stdout = StreamToLogger(logger, sys.stdout, logging.INFO)
    sys.stderr = StreamToLogger(logger, sys.stderr, logging.ERROR)

    logger.info("="*50)
    logger.info("🚀 KHỞI ĐỘNG BACKEND SPORT SEEKER")
    logger.info("="*50)

import uvicorn
import app.api.server

def main():
    multiprocessing.freeze_support()
    setup_logging()
    print("[SportSeeker] Starting Backend API on 127.0.0.1:10330...")
    uvicorn.run("app.api.server:app", host="127.0.0.1", port=10330, reload=False)

if __name__ == "__main__":
    main()
