import os
import sys
import shutil
import subprocess
import time
from pathlib import Path
from core_utils import run_cmd, kill_sport_seeker_processes, Logger

INSTALLER_DIR = Path(__file__).resolve().parent.parent
RESOURCE_DIR  = INSTALLER_DIR / "resource"
LOGS_DIR      = INSTALLER_DIR / "logs"

APPDATA     = Path(os.environ.get("APPDATA", ""))
USERPROFILE = Path(os.environ.get("USERPROFILE", ""))

INSTALL_ROOT = APPDATA / "SportSeeker"
APP_DIR      = INSTALL_ROOT / "app"
MODELS_DIR   = USERPROFILE / "SportSeeker" / "models"


# ----------------------------------------------------------------
# [2/6] Dọn dẹp phiên bản cũ (Giữ lại User Data)
# ----------------------------------------------------------------
def clean_old_installation():
    print("\n[2/6] Đang dọn dẹp phiên bản cũ (giữ lại dữ liệu người dùng)...")
    if not APP_DIR.exists():
        return

    # MẢNG QUAN TRỌNG: Khai báo tên các thư mục/file chứa dữ liệu người dùng cần giữ lại.
    KEEP_LIST = ["user_data", "database", "config.json", "db.sqlite3"]

    for item in APP_DIR.iterdir():
        if item.name in KEEP_LIST:
            print(f"  -> Giữ lại dữ liệu: {item.name}")
            continue
        try:
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink(missing_ok=True)
        except Exception as e:
            pass


# ----------------------------------------------------------------
# [3/6] Copy resource → AppData
# ----------------------------------------------------------------
def copy_resources():
    print("\n[3/6] Đang sao chép ứng dụng vào AppData...")
    
    print(f"-> Copy từ : {RESOURCE_DIR}")
    print(f"-> Đích    : {APP_DIR}")
    # Exclude models_bundle (deploy riêng ở bước tiếp theo)
    # dirs_exist_ok=True để copy đè lên mà không vướng các folder vừa giữ lại
    shutil.copytree(RESOURCE_DIR, APP_DIR, dirs_exist_ok=True, ignore=shutil.ignore_patterns("models_bundle"))
    print("-> Đã sao chép ứng dụng thành công.")


# ----------------------------------------------------------------
# [4/6] Deploy AI models từ bundle
# ----------------------------------------------------------------
def setup_models():
    print("\n[4/6] Đang kiểm tra và cài đặt kho dữ liệu AI Models...")
    bundle_dir = RESOURCE_DIR / "models_bundle"
    if not bundle_dir.exists():
        print("-> Không có models đính kèm. Ứng dụng sẽ tự tải qua OTA khi mở.")
        return

    # InsightFace
    if (bundle_dir / "models").exists():
        dest = MODELS_DIR / "models"
        os.makedirs(dest, exist_ok=True)
        shutil.copytree(bundle_dir / "models", dest, dirs_exist_ok=True)
        print("  + Đã cài đặt InsightFace Models.")

    # Paddle — chỉ deploy trên macOS, Windows dùng rapidocr-onnxruntime
    import platform as _platform
    if _platform.system() != "Windows":
        for folder in ["paddleocr", "paddlex", "paddle"]:
            src = bundle_dir / folder
            if src.exists():
                shutil.copytree(src, USERPROFILE / f".{folder}", dirs_exist_ok=True)
                print(f"  + Đã cài đặt {folder} Cache.")

    # HuggingFace
    hf_src = bundle_dir / "huggingface"
    if hf_src.exists():
        shutil.copytree(hf_src, USERPROFILE / ".cache" / "huggingface", dirs_exist_ok=True)
        print("  + Đã cài đặt HuggingFace Sentence Transformers.")

    print("-> Đã nạp AI Models vào hệ thống hoàn tất.")


# ----------------------------------------------------------------
# [5/6] Setup Python venv + pip install
# ----------------------------------------------------------------
def _find_uv(backend_dir: Path) -> str:
    """
    Tìm uv theo thứ tự ưu tiên:
    1. uv.exe cạnh installer (INSTALLER_DIR) → copy vào backend_dir
    2. uv.exe đã có trong backend_dir
    3. uv trên PATH hệ thống
    """
    installer_uv = INSTALLER_DIR / "uv.exe"
    local_uv     = backend_dir / "uv.exe"

    if installer_uv.exists():
        shutil.copy(installer_uv, local_uv)

    if local_uv.exists():
        return str(local_uv)

    return "uv"


def _run_pip_install(uv_cmd: str, backend_dir: Path, env_vars: dict) -> int:
    """
    Chạy uv pip install vào đúng venv, với output streaming.
    uv.toml nằm trong backend_dir → uv tự đọc only-binary constraints.
    """
    venv_python = backend_dir / ".venv" / "Scripts" / "python.exe"
    process = subprocess.Popen(
        f'"{uv_cmd}" pip install --python "{venv_python}" -r requirements-windows.txt',
        shell=True,
        cwd=backend_dir,       # uv đọc uv.toml tại đây
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env_vars,
    )
    for line in process.stdout:
        stripped = line.strip()
        if stripped and not stripped.startswith("warning:") and not stripped.startswith("DEPRECATION"):
            print(line, end="")
    process.wait()
    return process.returncode


def setup_python_env():
    print("\n[5/6] Đang thiết lập môi trường AI Backend...")
    backend_dir = APP_DIR / "backend"
    uv_cmd = _find_uv(backend_dir)

    print("-> Đang khởi tạo Virtual Environment (Python 3.11)...")
    run_cmd(f'"{uv_cmd}" venv --python 3.11', cwd=backend_dir, quiet=True)

    print("-> Đang cài đặt thư viện lõi AI...")
    print("   (Quá trình này mất 5-15 phút tùy tốc độ mạng, vui lòng không đóng cửa sổ)")
    print()

    env_vars = os.environ.copy()
    env_vars["SPORT_SEEKER_MODELS_ROOT"] = str(MODELS_DIR)
    env_vars["INSIGHTFACE_HOME"]         = str(MODELS_DIR)
    env_vars["HF_HOME"]                  = str(USERPROFILE / ".cache" / "huggingface")
    env_vars["KMP_DUPLICATE_LIB_OK"]     = "TRUE"
    env_vars["PYTHONUTF8"]               = "1"

    returncode = _run_pip_install(uv_cmd, backend_dir, env_vars)

    if returncode != 0:
        print()
        print("=" * 55)
        print("  [LỖI] Cài đặt thư viện AI thất bại.")
        print()
        print("  Nguyên nhân phổ biến:")
        print("  1. Mất kết nối Internet trong quá trình cài.")
        print("  2. Visual C++ Build Tools chưa được cài đúng.")
        print("     -> Thử chạy lại install_sport_seeker.bat")
        print("  3. Antivirus chặn quá trình biên dịch.")
        print("     -> Tắt tạm Antivirus rồi chạy lại.")
        print()
        print(f"  Log chi tiết: {LOGS_DIR / 'install_detail.log'}")
        print("=" * 55)
        sys.exit(1)

    print()
    print("-> Môi trường AI đã sẵn sàng.")


# ----------------------------------------------------------------
# [6/6] Tạo shortcut
# ----------------------------------------------------------------
def create_shortcuts():
    print("\n[6/6] Đang tạo lối tắt truy cập...")
    desktop    = USERPROFILE / "Desktop" / "Sport Seeker.lnk"
    start_menu = (
        Path(os.environ.get("APPDATA", ""))
        / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Sport Seeker.lnk"
    )
    target = APP_DIR / "sport_seeker.exe"

    ps_script = (
        f"$sh = New-Object -ComObject WScript.Shell; "
        f"$s = $sh.CreateShortcut('{desktop}'); "
        f"$s.TargetPath = '{target}'; "
        f"$s.WorkingDirectory = '{APP_DIR}'; "
        f"$s.Save(); "
        f"$s2 = $sh.CreateShortcut('{start_menu}'); "
        f"$s2.TargetPath = '{target}'; "
        f"$s2.WorkingDirectory = '{APP_DIR}'; "
        f"$s2.Save()"
    )
    run_cmd(f'powershell -Command "{ps_script}"', quiet=True)
    print("-> Đã tạo lối tắt ngoài Desktop và Start Menu.")


# ----------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------
if __name__ == "__main__":
    os.makedirs(LOGS_DIR, exist_ok=True)
    sys.stdout = Logger(LOGS_DIR / "install_detail.log")
    sys.stderr = sys.stdout

    print("===================================================")
    print("🚀 SPORT SEEKER - TRÌNH CÀI ĐẶT TỰ ĐỘNG (PYTHON)")
    print("===================================================")

    try:
        print("\n[1/6] Đang kiểm tra trạng thái hệ thống...")
        kill_sport_seeker_processes("Windows", quiet=True)
        time.sleep(2)

        clean_old_installation()
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
