import os
import sys
import platform
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.core.config import settings

class StreamToLogger:
    """Điều hướng stdout và stderr (print, lỗi báo đỏ) vào file log"""
    def __init__(self, logger, original_stream, log_level):
        self.logger = logger
        self.original_stream = original_stream
        self.log_level = log_level
        self._is_logging = False 

    def write(self, message):
        if message.strip() and not self._is_logging:
            self._is_logging = True 
            try:
                self.logger.log(self.log_level, message.strip())
            except Exception:
                pass 
            finally:
                self._is_logging = False 

        try:
            self.original_stream.write(message)
            self.original_stream.flush()
        except (UnicodeEncodeError, Exception):
            try:
                safe_msg = message.encode('ascii', errors='ignore').decode('ascii')
                self.original_stream.write(safe_msg)
                self.original_stream.flush()
            except:
                pass

    def flush(self):
        try:
            self.original_stream.flush()
        except:
            pass

    def __getattr__(self, attr):
        return getattr(self.original_stream, attr)


def _log_system_info(logger):
    """Ghi thông tin phần cứng, HĐH và version app vào log để chẩn đoán"""
    app_version = "Unknown"
    try:
        # Đường dẫn từ app/core/logger.py lùi ra root folder
        root_dir = Path(__file__).resolve().parent.parent.parent
        version_file = root_dir / "version.json"
        if version_file.exists():
            with open(version_file, "r", encoding="utf-8") as f:
                app_version = json.load(f).get("version", "Unknown")
    except Exception:
        pass

    logger.info("="*50)
    logger.info("🚀 KHỞI ĐỘNG BACKEND SPORT SEEKER")
    logger.info("="*50)
    logger.info("--- THÔNG TIN HỆ THỐNG GỠ LỖI ---")
    logger.info(f"Version App  : v{app_version}")
    logger.info(f"Hệ Điều Hành : {platform.system()} {platform.release()} ({platform.version()})")
    logger.info(f"Kiến trúc CPU: {platform.machine()} ({platform.architecture()[0]})")
    logger.info(f"Python Ver   : {platform.python_version()}")
    logger.info(f"ONNX Provider: {settings.ONNX_PROVIDER} ({settings.ONNX_PROVIDER_REASON})")
    logger.info("---------------------------------")


def setup_logging():
    """Khởi tạo và cấu hình logging toàn cục cho Backend"""
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
    
    # Tránh bị nhân đôi handler nếu setup_logging vô tình được gọi nhiều lần
    if not logger.handlers:
        logger.addHandler(handler)

    _log_system_info(logger)

    sys.stdout = StreamToLogger(logger, sys.stdout, logging.INFO)
    sys.stderr = StreamToLogger(logger, sys.stderr, logging.ERROR)
