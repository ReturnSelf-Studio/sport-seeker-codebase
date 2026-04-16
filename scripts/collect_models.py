import os
import sys
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"

def get_env(key, default=""):
    if not ENV_FILE.exists(): return default
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith(key):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return default

def copy_if_exists(src, dest):
    """Hàm helper copy nếu đường dẫn tồn tại"""
    if src.exists() and src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True)
        return True
    return False

def run_collection():
    print("\n===================================================")
    print("   🔍 DEEP SCANNING AI MODELS FOR OTA UPDATE")
    print("===================================================")

    staging_dir = ROOT_DIR / "build" / "models_staging"
    zip_out = ROOT_DIR / "build" / "offline_models_payload" # shutil tự động thêm .zip

    if staging_dir.exists():
        shutil.rmtree(staging_dir, ignore_errors=True)
    staging_dir.mkdir(parents=True, exist_ok=True)

    home = Path.home()
    env_dir_str = get_env("LOCAL_MODELS_SOURCE_DIR")
    env_dir = Path(env_dir_str) if env_dir_str else None

    print("⏳ [1/3] Đang tìm kiếm InsightFace (buffalo_l)...")
    insight_dest = staging_dir / "models" / "buffalo_l"
    insight_paths = []

    if env_dir:
        insight_paths.extend([env_dir / "models" / "buffalo_l", env_dir / "buffalo_l"])

    insight_paths.extend([
        ROOT_DIR / "models" / "models" / "buffalo_l",          # Thư mục models trong project gốc
        ROOT_DIR / "models" / "buffalo_l",
        home / ".insightface" / "models" / "buffalo_l",        # Cache hệ thống
        home / "SportSeeker" / "models" / "models" / "buffalo_l" # Cache của app đã chạy
    ])

    insight_found = False
    for p in insight_paths:
        if copy_if_exists(p, insight_dest):
            print(f"  -> ✅ Đã lấy từ: {p}")
            insight_found = True
            break # Tìm thấy ở ưu tiên cao nhất thì dừng quét

    if not insight_found:
        print("  -> ❌ BỎ QUA: Không tìm thấy InsightFace!")

    print("⏳ [2/3] Đang tìm kiếm PaddleOCR...")
    paddle_found = False

    custom_paddle_paths = []
    if env_dir:
        custom_paddle_paths.append(env_dir / "paddleocr")
    custom_paddle_paths.append(ROOT_DIR / "models" / "paddleocr")

    for p in custom_paddle_paths:
        if copy_if_exists(p, staging_dir / "paddleocr"):
            print(f"  -> ✅ Đã lấy từ: {p}")
            paddle_found = True
            break

    for p_name in [".paddleocr", ".paddlex", ".paddle"]:
        p = home / p_name
        if copy_if_exists(p, staging_dir / p_name.replace(".", "")): # Lưu thành paddleocr, paddlex
            print(f"  -> ✅ Đã lấy từ System Cache: {p}")
            paddle_found = True

    if not paddle_found:
        print("  -> ❌ BỎ QUA: Không tìm thấy thư mục PaddleOCR nào!")

    print("⏳ [3/3] Đang tìm kiếm HuggingFace (SentenceTransformers)...")
    hf_dest = staging_dir / "huggingface" / "hub" / "models--sentence-transformers--all-MiniLM-L6-v2"
    hf_paths = []

    if env_dir:
        hf_paths.extend([
            env_dir / "huggingface" / "hub" / "models--sentence-transformers--all-MiniLM-L6-v2",
            env_dir / "models--sentence-transformers--all-MiniLM-L6-v2"
        ])

    hf_paths.extend([
        ROOT_DIR / "models" / "huggingface" / "hub" / "models--sentence-transformers--all-MiniLM-L6-v2",
        home / ".cache" / "huggingface" / "hub" / "models--sentence-transformers--all-MiniLM-L6-v2",
        home / "SportSeeker" / "models" / "huggingface" / "hub" / "models--sentence-transformers--all-MiniLM-L6-v2"
    ])

    hf_found = False
    for p in hf_paths:
        if copy_if_exists(p, hf_dest):
            print(f"  -> ✅ Đã lấy từ: {p}")
            hf_found = True
            break

    if not hf_found:
        print("  -> ❌ BỎ QUA: Không tìm thấy HuggingFace!")

    print(f"\n📦 Đang nén các models thành file ZIP...")
    if Path(f"{zip_out}.zip").exists():
        Path(f"{zip_out}.zip").unlink()

    shutil.make_archive(str(zip_out), 'zip', str(staging_dir))

    shutil.rmtree(staging_dir, ignore_errors=True)

    print(f"🎉 THÀNH CÔNG! File Models Zip đã sẵn sàng tại: build/offline_models_payload.zip")

if __name__ == "__main__":
    run_collection()
