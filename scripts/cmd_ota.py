import os
import sys
from cli_config import (
    OS_NAME, RELEASE_DATA_DIR, RELEASE_MODELS_DIR, BACKEND_ASSET_DIR, ROOT_DIR,
    get_env, chunk_file, run_cmd
)

def chunk_backend(version="1.0.0"):
    print("\n===================================================")
    print("   📦 CHUNK BACKEND PAYLOAD (OTA UPDATE)")
    print("===================================================")
    base_url = get_env("BACKEND_UPDATE_URL")
    if base_url and not base_url.endswith("/"):
        base_url += "/"

    folder_name = "windows" if OS_NAME == "Windows" else "macos"
    out_dir = RELEASE_DATA_DIR / folder_name
    platform_base_url = base_url + folder_name + "/" if base_url else ""

    chunk_file(BACKEND_ASSET_DIR / "api_payload.zip", out_dir, platform_base_url, "version.json", version)

def chunk_models(version="1.0.0"):
    print("\n===================================================")
    print("   🧠 CHUNK AI MODELS (OTA UPDATE)")
    print("===================================================")

    source_zip = ROOT_DIR / "build" / "offline_models_payload.zip"
    if not source_zip.exists():
        print(f"⚠️ Không tìm thấy file {source_zip}.")
        print("👉 Đang tự động gọi lệnh 'collect-models' trước khi chunk...")
        run_cmd(f"{sys.executable} scripts/collect_models.py")

    base_url = get_env("MODELS_UPDATE_URL")

    print("\n⏳ Đang chia nhỏ (Chunk) file models.zip...")
    chunk_file(source_zip, RELEASE_MODELS_DIR, base_url, "models_version.json", version)
    print("\n✅ XONG TOÀN BỘ QUÁ TRÌNH OTA CHO MODEL!")
