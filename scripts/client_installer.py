import os
import sys
import shutil
import subprocess
import time
from pathlib import Path
from core_utils import run_cmd, kill_sport_seeker_processes, Logger

INSTALLER_DIR = Path(__file__).resolve().parent.parent
RESOURCE_DIR = INSTALLER_DIR / "resource"
LOGS_DIR = INSTALLER_DIR / "logs"

APPDATA = Path(os.environ.get("APPDATA", ""))
USERPROFILE = Path(os.environ.get("USERPROFILE", ""))

INSTALL_ROOT = APPDATA / "SportSeeker"
APP_DIR = INSTALL_ROOT / "app"
MODELS_DIR = USERPROFILE / "SportSeeker" / "models"

def copy_resources():
    print("\n[2/5] Đang sao chép ứng dụng vào AppData...")
    if APP_DIR.exists():
        print("-> Đang xóa phiên bản cũ (nếu có)...")
        shutil.rmtree(APP_DIR, ignore_errors=True)
    
    print(f"-> Đang copy từ: {RESOURCE_DIR.name}/")
    print(f"-> Đích đến: {APP_DIR}")
    shutil.copytree(RESOURCE_DIR, APP_DIR, ignore=shutil.ignore_patterns('models_bundle'))
    print("-> Đã sao chép ứng dụng thành công.")

def setup_models():
    print("\n[3/5] Đang kiểm tra và cài đặt kho dữ liệu AI Models...")
    bundle_dir = RESOURCE_DIR / "models_bundle"
    if not bundle_dir.exists():
        print("-> Không có models đính kèm. Ứng dụng sẽ tự tải qua OTA khi mở.")
        return

    if (bundle_dir / "models").exists():
        dest = MODELS_DIR / "models"
        os.makedirs(dest, exist_ok=True)
        shutil.copytree(bundle_dir / "models", dest, dirs_exist_ok=True)
        print("  + Đã cài đặt InsightFace Models.")

    for folder in ["paddleocr", "paddlex"]:
        src = bundle_dir / folder
        if src.exists():
            shutil.copytree(src, USERPROFILE / f".{folder}", dirs_exist_ok=True)
            print(f"  + Đã cài đặt {folder} Cache.")

    hf_src = bundle_dir / "huggingface"
    if hf_src.exists():
        shutil.copytree(hf_src, USERPROFILE / ".cache" / "huggingface", dirs_exist_ok=True)
        print("  + Đã cài đặt HuggingFace Sentence Transformers.")
    
    print("-> Đã nạp AI Models vào hệ thống hoàn tất.")

def setup_python_env():
    print("\n[4/5] Đang thiết lập môi trường AI Backend...")
    backend_dir = APP_DIR / "backend"

    uv_cmd = "uv"
    if (INSTALLER_DIR / "uv.exe").exists():
        shutil.copy(INSTALLER_DIR / "uv.exe", backend_dir / "uv.exe")
        uv_cmd = str(backend_dir / "uv.exe")

    print("-> Đang khởi tạo Virtual Environment...")
    run_cmd(f"{uv_cmd} venv --python 3.11", cwd=backend_dir, quiet=True)
    
    print("-> Đang cài đặt thư viện lõi (Quá trình này mất từ 2-5 phút, không được đóng cửa sổ)...")
    env_vars = os.environ.copy()
    env_vars["SPORT_SEEKER_MODELS_ROOT"] = str(MODELS_DIR)

    process = subprocess.Popen(
        f"{uv_cmd} pip install -r requirements-windows.txt",
        shell=True, cwd=backend_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env_vars
    )
    for line in process.stdout:
        print(line, end="")
    process.wait()
    
    if process.returncode != 0:
        print("\n[LỖI] Cài đặt thư viện AI thất bại.")
        sys.exit(1)
    print("-> Môi trường AI đã sẵn sàng.")

def create_shortcuts():
    print("\n[5/5] Đang tạo lối tắt truy cập...")
    desktop = USERPROFILE / "Desktop" / "Sport Seeker.lnk"
    start_menu = Path(os.environ.get("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Sport Seeker.lnk"
    target = APP_DIR / "sport_seeker.exe"
    
    ps_script = f"""
    $sh = New-Object -ComObject WScript.Shell
    $s = $sh.CreateShortcut('{desktop}')
    $s.TargetPath = '{target}'
    $s.WorkingDirectory = '{APP_DIR}'
    $s.Save()
    
    $s2 = $sh.CreateShortcut('{start_menu}')
    $s2.TargetPath = '{target}'
    $s2.WorkingDirectory = '{APP_DIR}'
    $s2.Save()
    """
    run_cmd(f'powershell -Command "{ps_script}"', quiet=True)
    print("-> Đã tạo lối tắt ngoài Desktop và Start Menu.")

if __name__ == "__main__":
    # 1. Chuyển hướng stdout/stderr để vừa hiện console vừa lưu file log
    os.makedirs(LOGS_DIR, exist_ok=True)
    sys.stdout = Logger(LOGS_DIR / "install_detail.log")
    sys.stderr = sys.stdout
    
    print("===================================================")
    print("🚀 SPORT SEEKER - TRÌNH CÀI ĐẶT TỰ ĐỘNG (PYTHON)")
    print("===================================================")
    try:
        print("\n[1/5] Đang kiểm tra trạng thái hệ thống...")
        kill_sport_seeker_processes("Windows", quiet=True) 
        time.sleep(2)
        
        copy_resources()
        setup_models()
        setup_python_env()
        create_shortcuts()
        
        print("\n===================================================")
        print("🎉 CÀI ĐẶT THÀNH CÔNG! BẠN CÓ THỂ MỞ ỨNG DỤNG NGOÀI DESKTOP.")
        print("===================================================")
    except Exception as e:
        print(f"\n❌ LỖI NGHIÊM TRỌNG: {e}")
        print(f"Chi tiết lỗi đã được lưu tại: {LOGS_DIR / 'install_detail.log'}")
        sys.exit(1)