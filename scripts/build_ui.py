import os
import sys
import shutil
import platform
from pathlib import Path

# Dùng chính config của bạn
from cli_config import ROOT_DIR, FRONTEND_DIR
from core_utils import run_cmd

def build_ui_macos():
    if platform.system() != "Darwin":
        print("❌ Lỗi: Script build_ui.py hiện tại chỉ được cấu hình cho macOS.")
        print("👉 Trên Windows, hệ thống sẽ tự động gọi build_windows.py.")
        sys.exit(1)

    print("\n===================================================")
    print(f"   🚀 BUILD FLUTTER UI & PACKAGING (macOS Launcher)")
    print("===================================================")

    print("\n[0] Cập nhật Build Number & Môi trường...")
    run_cmd(f"{sys.executable} scripts/increment_build.py")
    run_cmd(f"{sys.executable} scripts/generate_env_dart.py")
    
    # BƯỚC 1: BUILD PDF TỪ MARKDOWN
    print("\n[1] Đang tạo file PDF Hướng dẫn sử dụng...")
    run_cmd(f"{sys.executable} scripts/build_installation_guide_pdf.py -i docs/ -o dist/pdf/ -a assets/")

    print("\n[2] Dọn dẹp & Tải thư viện Flutter...")
    run_cmd("flutter clean", cwd=FRONTEND_DIR)
    run_cmd("flutter pub get", cwd=FRONTEND_DIR)

    release_dir = ROOT_DIR / "SportSeeker_macOS_Release"
    shutil.rmtree(release_dir, ignore_errors=True)
    os.makedirs(release_dir, exist_ok=True)

    # BƯỚC 2: BUILD FLUTTER APP
    print("\n[3] Đang biên dịch Flutter App...")
    run_cmd("flutter build macos", cwd=FRONTEND_DIR)
    
    # Lấy App Bundle vừa build ra
    app_build_path = FRONTEND_DIR / "build" / "macos" / "Build" / "Products" / "Release" / "Sport Seeker.app"

    # BƯỚC 3: GOM VÀO THƯ MỤC RELEASE (KHÔNG INJECT BACKEND NỮA VÌ ĐÃ CÓ ZIP BÊN TRONG FLUTTER ASSETS)
    print("\n[4] Đang gom Tài liệu & App...")
    shutil.copytree(app_build_path, release_dir / "Sport Seeker.app", dirs_exist_ok=True)

    # Chép script cài đặt command
    cmd_script = ROOT_DIR / "scripts" / "install_sport_seeker.command"
    if cmd_script.exists():
        shutil.copy(cmd_script, release_dir)
        run_cmd(f"chmod +x '{release_dir}/install_sport_seeker.command'")

    # Chép file PDF
    pdf_guide = ROOT_DIR / "dist" / "pdf" / "installation_guide_macos.pdf"
    if pdf_guide.exists():
        shutil.copy(pdf_guide, release_dir)
        print("✅ Đã chép file Hướng dẫn sử dụng macOS.")
    else:
        print(f"⚠️ Cảnh báo: Không tìm thấy file PDF tại {pdf_guide}.")

    # BƯỚC 4: NÉN ZIP TRẢ KHÁCH HÀNG
    zip_name = "SportSeeker_macOS"
    zip_path = ROOT_DIR / zip_name
    if os.path.exists(f"{zip_path}.zip"):
        os.remove(f"{zip_path}.zip")

    print(f"\n📦 [5] Đang nén file {zip_name}.zip cho khách hàng...")
    shutil.make_archive(str(zip_path), 'zip', str(release_dir))

    # Dọn dẹp thư mục tạm
    shutil.rmtree(release_dir, ignore_errors=True)
    print(f"🎉 HOÀN TẤT! File cài đặt Launcher đã sẵn sàng tại: {zip_path}.zip")

if __name__ == "__main__":
    build_ui_macos()
