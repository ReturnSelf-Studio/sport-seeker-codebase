import os
import sys
import platform
import json
import logging
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.core.config import settings

class StreamToLogger:
    """Điều hướng stdout và stderr (print, báo lỗi) vào file log an toàn"""
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
            # Fallback cực mạnh: nếu cmd không hỗ trợ ký tự lạ, ép kiểu sang ascii bỏ qua lỗi
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


def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """Bắt tất cả lỗi crash (Unhandled Exceptions) và ghi kèm stack trace"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger = logging.getLogger("SportSeekerBackend")
    logger.critical("[FATAL] [CRASH REPORT] LỖI HỆ THỐNG KHÔNG LƯỜNG TRƯỚC:", exc_info=(exc_type, exc_value, exc_traceback))


def _log_system_info(logger):
    """Ghi thông tin phần cứng, HĐH và toàn bộ version vào log để chẩn đoán"""
    os_name = f"{platform.system()} {platform.release()}"
    if platform.system() == "Windows":
        try:
            build = sys.getwindowsversion().build
            if build >= 22000:
                os_name = "Windows 11"
        except AttributeError:
            pass

    logger.info("==================================================")
    logger.info("[START] KHỞI ĐỘNG BACKEND SPORT SEEKER")
    logger.info("==================================================")
    logger.info("--- THÔNG TIN HỆ THỐNG ---")
    logger.info(f"Hệ Điều Hành : {os_name} (Build: {platform.version()})")
    logger.info(f"Kiến trúc CPU: {platform.machine()} ({platform.architecture()[0]})")
    logger.info(f"Python Ver   : {platform.python_version()}")
    logger.info(f"ONNX Provider: {settings.ONNX_PROVIDER} ({settings.ONNX_PROVIDER_REASON})")
    
    try:
        root_dir = Path(__file__).resolve().parent.parent.parent
        version_file = root_dir / "version.json"
        if version_file.exists():
            logger.info("--- THÔNG TIN PHIÊN BẢN ---")
            with open(version_file, "r", encoding="utf-8") as f:
                version_data = json.load(f)
                for key, value in version_data.items():
                    formatted_key = key.replace("_", " ").title()
                    logger.info(f"{formatted_key.ljust(20)}: {value}")
        else:
            logger.warning("[SYSTEM] Không tìm thấy file version.json tại thư mục gốc!")
    except Exception as e:
        logger.error(f"[SYSTEM] Lỗi khi đọc file version.json: {e}")

    logger.info("---------------------------------")


def setup_logging():
    """Khởi tạo và cấu hình logging toàn cục cho Backend"""
    if sys.platform == 'win32':
        log_dir = Path(os.environ.get('APPDATA', '')) / "SportSeeker" / "logs"
    else:
        log_dir = Path.home() / "SportSeeker" / "logs"
        
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "backend.log"

    handler = RotatingFileHandler(log_file, maxBytes=20*1024*1024, backupCount=5, encoding='utf-8')
    
    # FORMATTER tự động gắn Label [INFO], [ERROR], [WARNING] cho từng dòng log
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)

    logger = logging.getLogger("SportSeekerBackend")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        logger.addHandler(handler)

    sys.excepthook = handle_unhandled_exception

    _log_system_info(logger)

    sys.stdout = StreamToLogger(logger, sys.stdout, logging.INFO)
    sys.stderr = StreamToLogger(logger, sys.stderr, logging.ERROR)

    return logger
    