import shutil
import platform
import os
import sys
from pathlib import Path
from cli_config import ROOT_DIR
from collect_models import collect_models_into
from core_utils import run_cmd

FRONTEND_DIR = ROOT_DIR / "frontend"
PUBSPEC_FILE = FRONTEND_DIR / "pubspec.yaml"
PUBSPEC_BAK  = FRONTEND_DIR / "pubspec.yaml.bak"

# pyproject.toml minimal cho release — chỉ để uv run biết python version
RELEASE_PYPROJECT = """\
[project]
name = "sport-seeker-installer"
version = "1.0.0"
requires-python = "==3.11.*"
dependencies = []
"""

def build_windows():
    print("\n===================================================")
    print("   🚀 ĐÓNG GÓI RELEASE WINDOWS (SOURCE DISTRIBUTION)")
    print("===================================================")

    try:
        # --------------------------------------------------------
        # [0] Version
        # --------------------------------------------------------
        print("\n[0] Cập nhật Build Number...")
        run_cmd(f"{sys.executable} scripts/increment_build.py")
        run_cmd(f"{sys.executable} scripts/generate_env_dart.py")

        # --------------------------------------------------------
        # [1] Tối ưu pubspec
        # --------------------------------------------------------
        print("\n[1] Tối ưu pubspec.yaml...")
        shutil.copy(PUBSPEC_FILE, PUBSPEC_BAK)
        lines = PUBSPEC_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
        # Sửa thành api_payload. để cover cả .zip và .tar.gz
        PUBSPEC_FILE.write_text(
            "".join(l for l in lines if "assets/backend/api_payload." not in l),
            encoding="utf-8",
        )

        # --------------------------------------------------------
        # [2] Build Flutter
        # --------------------------------------------------------
        print("\n[2] Biên dịch Flutter...")
        run_cmd("flutter clean", cwd=FRONTEND_DIR)
        run_cmd("flutter pub get", cwd=FRONTEND_DIR)
        run_cmd("flutter build windows", cwd=FRONTEND_DIR)

        # --------------------------------------------------------
        # [3] Tạo cấu trúc dist
        # --------------------------------------------------------
        dist_dir = ROOT_DIR / "SportSeeker_Windows_Release"
        if dist_dir.exists():
            shutil.rmtree(dist_dir)

        resource_dir = dist_dir / "resource"
        tools_dir    = dist_dir / "tools"
        logs_dir     = dist_dir / "logs"
        resource_dir.mkdir(parents=True)
        tools_dir.mkdir(parents=True)
        logs_dir.mkdir(parents=True)

        print("\n[3] Sao chép Flutter UI và Backend...")

        # 3.1 Flutter UI
        flutter_release = FRONTEND_DIR / "build/windows/x64/runner/Release"
        shutil.copytree(flutter_release, resource_dir, dirs_exist_ok=True)

        # 3.2 Backend source
        backend_dest = resource_dir / "backend"
        backend_dest.mkdir()
        shutil.copy(ROOT_DIR / "main.py", backend_dest)
        shutil.copy(ROOT_DIR / "requirements-windows.txt", backend_dest)
        shutil.copytree(ROOT_DIR / "app", backend_dest / "app")

        # 3.3 uv.toml vào backend_dest
        uv_toml_src = ROOT_DIR / "uv.toml"
        if uv_toml_src.exists():
            shutil.copy(uv_toml_src, backend_dest / "uv.toml")
            print("  -> Đã nhúng uv.toml vào backend/.")
        else:
            print("  [CẢNH BÁO] Không tìm thấy uv.toml — only-binary sẽ không được áp dụng!")

        # --------------------------------------------------------
        # [4] Tools (installer + core_utils)
        # --------------------------------------------------------
        print("\n[4] Sao chép Bootstrapper & CLI Tools...")
        installer_src = ROOT_DIR / "scripts" / "client_installer.py"
        utils_src     = ROOT_DIR / "scripts" / "core_utils.py"
        if installer_src.exists() and utils_src.exists():
            shutil.copy(installer_src, tools_dir / "installer.py")
            shutil.copy(utils_src,     tools_dir / "core_utils.py")
        else:
            print("[CẢNH BÁO] Thiếu installer.py hoặc core_utils.py!")

        # --------------------------------------------------------
        # [5] AI Models bundle
        # --------------------------------------------------------
        print("\n[5] Thu thập kho AI Models Offline...")
        models_bundle_dir = resource_dir / "models_bundle"
        models_bundle_dir.mkdir(exist_ok=True)
        collect_models_into(models_bundle_dir)

        # --------------------------------------------------------
        # [5.5] Build PDF Hướng dẫn cài đặt
        # --------------------------------------------------------
        print("\n[5.5] Tự động tạo file PDF Hướng dẫn cài đặt...")
        run_cmd(f"{sys.executable} scripts/build_installation_guide_pdf.py -i docs/ -o docs/ -a assets/")

        # --------------------------------------------------------
        # [6] Root-level files cho .bat
        # --------------------------------------------------------
        print("\n[6] Chuẩn bị đóng gói...")

        shutil.copy(ROOT_DIR / "scripts/install_sport_seeker.bat", dist_dir / "install_sport_seeker.bat")
        shutil.copy(ROOT_DIR / "scripts/install_uv.ps1", dist_dir / "install_uv.ps1")
        shutil.copy(ROOT_DIR / "scripts/uninstall_sport_seeker.bat", dist_dir / "uninstall_sport_seeker.bat")

        (dist_dir / "pyproject.toml").write_text(RELEASE_PYPROJECT, encoding="utf-8")
        print("  -> Đã tạo pyproject.toml cho release.")

        clean_bat_src = ROOT_DIR / "scripts/clean.bat"
        if clean_bat_src.exists():
            shutil.copy(clean_bat_src, dist_dir / "clean.bat")
            print("  -> Đã nhúng clean.bat.")
        else:
            print("  [CẢNH BÁO] Không tìm thấy scripts/clean.bat!")

        pdf_guide = ROOT_DIR / "docs/installation_guide_windows.pdf"
        if pdf_guide.exists():
            shutil.copy(pdf_guide, dist_dir / "installation_guide_windows.pdf")

        # --------------------------------------------------------
        # [7] Zip
        # --------------------------------------------------------
        zip_output = ROOT_DIR / "SportSeeker_Windows"
        zip_output.with_suffix(".zip").unlink(missing_ok=True)
        print(f"\n[7] Đang nén thành {zip_output}.zip ...")
        shutil.make_archive(str(zip_output), "zip", str(dist_dir.parent), dist_dir.name)
        shutil.rmtree(dist_dir)
        print("\n🎉 HOÀN TẤT! File gửi khách: SportSeeker_Windows.zip")

    finally:
        if PUBSPEC_BAK.exists():
            print("\nKhôi phục pubspec.yaml nguyên bản...")
            shutil.move(PUBSPEC_BAK, PUBSPEC_FILE)

if __name__ == "__main__":
    if platform.system() != "Windows":
        print("❌ LỖI: Script này chỉ chạy trên môi trường Windows.")
    else:
        build_windows()
