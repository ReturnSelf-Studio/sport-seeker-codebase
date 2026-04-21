import os
import subprocess
import shutil
import sys
import glob
from cli_config import OS_NAME, BACKEND_ASSET_DIR, ROOT_DIR
from core_utils import run_cmd, kill_sport_seeker_processes

def build_backend():
    print("\n===================================================")
    print(f"   🚀 BUILD BACKEND BINARY ({OS_NAME})")
    print("===================================================")

    # Cai platform deps + dev tools cung luc
    platform_req = "requirements-windows.txt" if OS_NAME == "Windows" else "requirements-macos-arm64.txt"
    run_cmd(f"uv pip install -r {platform_req} -r requirements-dev.txt")

    os.makedirs(BACKEND_ASSET_DIR, exist_ok=True)

    extra_params = ""
    if OS_NAME == "Windows":
        site_pkgs = os.path.join(str(ROOT_DIR), ".venv", "Lib", "site-packages")

        dll_dirs = {
            "faiss": os.path.join(site_pkgs, "faiss"),
            "faiss.libs": os.path.join(site_pkgs, "faiss.libs"),
            "numpy.libs": os.path.join(site_pkgs, "numpy.libs")
        }

        for dest_name, path in dll_dirs.items():
            if os.path.exists(path):
                dll_files = glob.glob(os.path.join(path, "*.dll"))
                for dll_file in dll_files:
                    dll_safe = dll_file.replace("\\", "/")
                    extra_params += f' --add-binary "{dll_safe};{dest_name}"'
                    print(f"  -> Đã nạp DLL: {os.path.basename(dll_safe)} vào /{dest_name}")

    pyinstaller_cmd = (
        "uv run pyinstaller --name SportSeekerAPI "
        "--hidden-import insightface --hidden-import onnxruntime --hidden-import faiss "
        "--hidden-import faiss.swigfaiss --hidden-import faiss.swigfaiss_avx2 "
        "--hidden-import paddleocr --hidden-import sentence_transformers --hidden-import cv2 "
        "--hidden-import numpy --hidden-import pyarrow --hidden-import multipart "
        "--collect-data Cython --collect-all paddleocr --copy-metadata paddleocr "
        "--collect-data insightface --collect-all faiss --collect-binaries faiss "
        f"{extra_params} "
        f"--distpath {BACKEND_ASSET_DIR} --workpath build --noconfirm main.py"
    )

    run_cmd(pyinstaller_cmd)

    api_dir = BACKEND_ASSET_DIR / "SportSeekerAPI"
    zip_path = BACKEND_ASSET_DIR / "api_payload"
    if os.path.exists(f"{zip_path}.zip"):
        os.remove(f"{zip_path}.zip")

    print(f"📦 Đang nén thư mục {api_dir}...")
    shutil.make_archive(str(zip_path), 'zip', str(api_dir))

    shutil.rmtree(api_dir, ignore_errors=True)
    print(f"✅ XONG! Binary đã được nén tại: {zip_path}.zip")

def kill_backend():
    kill_sport_seeker_processes()
