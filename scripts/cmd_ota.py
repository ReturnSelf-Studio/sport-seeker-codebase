import os
import sys
from cli_config import (
    RELEASE_MODELS_DIR, ROOT_DIR,
    get_env, chunk_file
)
from core_utils import run_cmd

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
