import os
import shutil
from pathlib import Path
from cli_config import OS_NAME
from cmd_backend import kill_backend

def clean_all():
    print("\n===================================================")
    print(f"   🧹 CLEANUP SCRIPT ({OS_NAME})")
    print("===================================================")
    kill_backend()

    home = Path.home()
    shutil.rmtree(home / "SportSeeker", ignore_errors=True)
    shutil.rmtree(home / ".paddlex", ignore_errors=True)
    shutil.rmtree(home / ".paddleocr", ignore_errors=True)

    if OS_NAME == "Windows":
        for base in [Path(os.environ.get("APPDATA", home)), Path(os.environ.get("LOCALAPPDATA", home))]:
            shutil.rmtree(base / "com.example/sportSeeker", ignore_errors=True)
            shutil.rmtree(base / "com.aibus/sportSeeker", ignore_errors=True)
            shutil.rmtree(base / "sport_seeker", ignore_errors=True)
    else:
        lib_support = home / "Library/Application Support"
        shutil.rmtree(lib_support / "com.example.sportSeeker", ignore_errors=True)
        shutil.rmtree(lib_support / "com.aibus.sportSeeker", ignore_errors=True)
        shutil.rmtree(lib_support / "sport_seeker", ignore_errors=True)
    print("✅ HOÀN TẤT! Dữ liệu cũ đã được xóa sạch.")
