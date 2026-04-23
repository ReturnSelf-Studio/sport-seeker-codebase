import json
import os
import sys
from cli_config import (
    VERSION_FILE, ROOT_DIR, RELEASE_MODELS_DIR,
    get_file_hash
)
from cmd_ota import chunk_models
from core_utils import run_cmd

def pre_commit():
    print("===================================================")
    print("🚀 CHẠY PRE-COMMIT HOOKS...")
    print("===================================================")
    res = run_cmd("git branch --show-current", capture_output=True)

    if res.stdout.strip() == "main":
        if not VERSION_FILE.exists():
            print("⚠️ Không tìm thấy release_info.json, sử dụng version mặc định.")
            model_ver = "1.0.0"
        else:
            info = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
            model_ver = info.get("model_version", "1.0.0")

        print(f"🏷️ Phiên bản chuẩn bị Release - Model: {model_ver}")

        print("\n⏳ Kiểm tra sự thay đổi của AI Models bằng SHA256...")
        run_cmd(f"{sys.executable} scripts/collect_models.py")

        source_zip = ROOT_DIR / "build" / "offline_models_payload.zip"
        if not source_zip.exists():
            print(f"❌ Thu thập Model thất bại.")
            sys.exit(1)

        current_hash = get_file_hash(source_zip)
        hash_file = RELEASE_MODELS_DIR / ".model_hash"

        old_hash = ""
        if hash_file.exists():
            old_hash = hash_file.read_text(encoding="utf-8").strip()

        if current_hash != old_hash:
            print(f"🔄 Phát hiện Model thay đổi (Hash mới: {current_hash[:8]}). Tiến hành cắt nhỏ Models...")
            chunk_models(model_ver)
            os.makedirs(RELEASE_MODELS_DIR, exist_ok=True)
            hash_file.write_text(current_hash, encoding="utf-8")
            run_cmd(f"git add {RELEASE_MODELS_DIR}/")
        else:
            print(f"⏭️ Models không có sự thay đổi (Trùng Hash: {current_hash[:8]}).")
            print("👉 Bỏ qua cắt nhỏ Models để tiết kiệm thời gian.")

        if VERSION_FILE.exists():
            run_cmd("git add version.json")

        print("\n✅ PRE-COMMIT HOÀN TẤT, SẴN SÀNG COMMIT!")
    else:
        print("⏭️ Không phải nhánh main, bỏ qua quy trình Auto-Release.")
