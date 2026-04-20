import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
from core_utils import run_cmd

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

def build_ui_macos():
    if platform.system() != "Darwin":
        print("❌ Lỗi: Script build_ui.py hiện tại chỉ được cấu hình cho macOS.")
        print("👉 Trên Windows, hệ thống sẽ tự động gọi build_windows.py.")
        sys.exit(1)

    print("\n===================================================")
    print(f"   🚀 BUILD FLUTTER UI & PACKAGING (macOS)")
    print("===================================================")

    print("\n[0] Cập nhật Build Number...")
    run_cmd(f"{sys.executable} scripts/increment_build.py")
    run_cmd(f"{sys.executable} scripts/generate_env_dart.py")
    
    run_cmd("flutter clean", cwd=FRONTEND_DIR)
    run_cmd("flutter pub get", cwd=FRONTEND_DIR)

    release_dir = ROOT_DIR / "SportSeeker_macOS_Release"
    shutil.rmtree(release_dir, ignore_errors=True)
    os.makedirs(release_dir, exist_ok=True)

    run_cmd("flutter build macos", cwd=FRONTEND_DIR)
    shutil.copytree(FRONTEND_DIR / "build/macos/Build/Products/Release/Sport Seeker.app", release_dir / "Sport Seeker.app", dirs_exist_ok=True)

    cmd_script = ROOT_DIR / "scripts/install_sport_seeker.command"
    if cmd_script.exists():
        shutil.copy(cmd_script, release_dir)
        run_cmd(f"chmod +x '{release_dir}/install_sport_seeker.command'")

    pdf_guide = ROOT_DIR / "docs/installation_guide_macos.pdf"
    if pdf_guide.exists():
        shutil.copy(pdf_guide, release_dir)

    zip_name = "SportSeeker_macOS"
    if os.path.exists(f"{zip_name}.zip"):
        os.remove(f"{zip_name}.zip")

    print(f"\n📦 Đang nén file {zip_name}.zip...")
    shutil.make_archive(zip_name, 'zip', str(release_dir))

    shutil.rmtree(release_dir, ignore_errors=True)
    print(f"🎉 HOÀN TẤT! File cài đặt đã sẵn sàng tại: {ROOT_DIR / zip_name}.zip")

if __name__ == "__main__":
    build_ui_macos()
