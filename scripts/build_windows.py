import os
import shutil
import subprocess
import platform
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FLUTTER_UI_DIR = ROOT_DIR / "flutter_ui"
PUBSPEC_FILE = FLUTTER_UI_DIR / "pubspec.yaml"
PUBSPEC_BAK = FLUTTER_UI_DIR / "pubspec.yaml.bak"

def run_cmd(cmd, cwd=None):
    print(f"\n> Running: {cmd}")
    subprocess.run(cmd, shell=True, cwd=cwd or ROOT_DIR, check=True)

def build_windows():
    print("\n===================================================")
    print("   🚀 ĐÓNG GÓI RELEASE WINDOWS (AUTOMATED FLOW)")
    print("===================================================")

    try:
        print("⏳ [1] Đang tối ưu hóa pubspec.yaml...")
        shutil.copy(PUBSPEC_FILE, PUBSPEC_BAK) # Backup

        with open(PUBSPEC_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        with open(PUBSPEC_FILE, "w", encoding="utf-8") as f:
            for line in lines:
                if "assets/backend/api_payload.zip" not in line:
                    f.write(line)

        print("⏳ [2] Đang biên dịch giao diện Flutter...")
        run_cmd("flutter clean", cwd=FLUTTER_UI_DIR)
        run_cmd("flutter pub get", cwd=FLUTTER_UI_DIR)
        run_cmd("flutter build windows", cwd=FLUTTER_UI_DIR)

        release_name = "SportSeeker_Windows_Release"
        dist_dir = ROOT_DIR / release_name
        if dist_dir.exists(): shutil.rmtree(dist_dir)

        resource_dir = dist_dir / "resource"
        os.makedirs(resource_dir)

        flutter_release = FLUTTER_UI_DIR / "build/windows/x64/runner/Release"
        shutil.copytree(flutter_release, resource_dir, dirs_exist_ok=True)

        backend_dest = resource_dir / "backend"
        os.makedirs(backend_dest)
        shutil.copy(ROOT_DIR / "main.py", backend_dest)
        shutil.copy(ROOT_DIR / "requirements-windows.txt", backend_dest)
        shutil.copytree(ROOT_DIR / "app", backend_dest / "app")

        shutil.copy(ROOT_DIR / "scripts/install_sport_seeker.bat", dist_dir / "install_sport_seeker.bat")
        pdf_guide = ROOT_DIR / "docs/installation_guide_windows.pdf"
        if pdf_guide.exists():
            shutil.copy(pdf_guide, dist_dir / "installation_guide_windows.pdf")

        zip_output = ROOT_DIR / "SportSeeker_Windows"
        if os.path.exists(f"{zip_output}.zip"): os.remove(f"{zip_output}.zip")

        print(f"\n📦 Đang tạo file nén {zip_output}.zip...")
        shutil.make_archive(str(zip_output), 'zip', str(dist_dir))

        shutil.rmtree(dist_dir)
        print(f"🎉 HOÀN TẤT! File gửi khách: SportSeeker_Windows.zip")

    finally:
        if PUBSPEC_BAK.exists():
            print("🔄 Đang khôi phục pubspec.yaml nguyên bản cho môi trường Dev...")
            shutil.move(PUBSPEC_BAK, PUBSPEC_FILE)

if __name__ == "__main__":
    if platform.system() != "Windows":
        print("❌ Script này chỉ chạy trên Windows.")
    else:
        build_windows()
