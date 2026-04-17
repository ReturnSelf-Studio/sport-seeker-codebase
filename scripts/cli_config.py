import os
import sys
import shutil
import platform
import subprocess
import hashlib
import json
import math
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"
FLUTTER_UI_DIR = ROOT_DIR / "flutter_ui"
BACKEND_ASSET_DIR = FLUTTER_UI_DIR / "assets" / "backend"
RELEASE_DATA_DIR = ROOT_DIR / "release_data"
RELEASE_MODELS_DIR = ROOT_DIR / "release_models"
RELEASE_INFO_FILE = ROOT_DIR / "release_info.json"

OS_NAME = platform.system()

def get_file_hash(filepath):
    """Tính mã băm SHA256 của một file"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_env(key, default=""):
    """Đọc biến môi trường từ file .env"""
    if not ENV_FILE.exists(): return default
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith(key):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return default

def copy_dir(src: Path, dst: Path) -> bool:
    """Copy src -> dst nếu src là directory. Trả về True nếu thành công."""
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
        return True
    return False


def copy_first_found(candidates: list[Path], dst: Path, label: str) -> bool:
    """Copy path đầu tiên tìm thấy trong candidates vào dst. Dừng sớm."""
    for src in candidates:
        if copy_dir(src, dst):
            print(f"  -> OK: {src}")
            return True
    print(f"  -> SKIP: Khong tim thay {label}.")
    return False


def copy_all_found(candidates: list[tuple[Path, Path]], label: str) -> bool:
    """Copy tất cả các cặp (src, dst) tìm thấy — không dừng sớm."""
    found = False
    for src, dst in candidates:
        if copy_dir(src, dst):
            print(f"  -> OK: {src}")
            found = True
    if not found:
        print(f"  -> SKIP: Khong tim thay {label}.")
    return found


def check_env():
    print("⏳ [1] Kiểm tra cấu hình môi trường (.env)...")
    if not ENV_FILE.exists():
        print("⚠️ Không tìm thấy file .env! Vui lòng tạo file .env tại root project.")
        sys.exit(1)
    print("✅ Cấu hình môi trường hợp lệ.")

def chunk_file(source_zip, out_dir, base_url, json_filename, version="1.0.0"):
    """Chia nhỏ file zip thành các chunk 25MB cho OTA"""
    if not os.path.exists(source_zip):
        print(f"❌ Không tìm thấy {source_zip}")
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f != ".model_hash":
            os.remove(os.path.join(out_dir, f))

    chunk_size = 25 * 1024 * 1024 # 25MB
    file_size = os.path.getsize(source_zip)
    total_chunks = math.ceil(file_size / chunk_size)
    chunks_list = []

    print(f"📦 Đang chia nhỏ {file_size / (1024*1024):.1f} MB thành {total_chunks} phần...")

    with open(source_zip, 'rb') as infile:
        for i in range(total_chunks):
            chunk_data = infile.read(chunk_size)
            chunk_name = f"payload.part{i:03d}"
            with open(os.path.join(out_dir, chunk_name), 'wb') as outfile:
                outfile.write(chunk_data)
            chunks_list.append(chunk_name)

    if base_url and not base_url.endswith("/"): base_url += "/"
    version_info = {"version": version, "base_url": base_url, "chunks": chunks_list}
    with open(os.path.join(out_dir, json_filename), 'w') as f:
        json.dump(version_info, f, indent=2)
    print(f"✅ Đã tạo xong thư mục {out_dir}/")
