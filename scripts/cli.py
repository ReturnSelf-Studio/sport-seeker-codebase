import sys
import argparse
import platform
from cli_config import check_env
from cmd_backend import build_backend, kill_backend
from cmd_ota import chunk_backend, chunk_models
from cmd_system import clean_all
from cmd_hooks import pre_commit
from core_utils import run_cmd

def generate_env_dart():
    print("⏳ [2] Đang tự động tạo env.dart từ .env...")
    run_cmd(f"{sys.executable} scripts/generate_env_dart.py")

def collect_models():
    run_cmd(f"{sys.executable} scripts/collect_models.py")

def build_ui():
    """Luồng build UI thuần túy cho macOS"""
    run_cmd(f"{sys.executable} scripts/build_ui.py")

def build_windows():
    """Luồng build + đóng gói Source Dist thuần túy cho Windows"""
    run_cmd(f"{sys.executable} scripts/build_windows.py")

def build_all():
    """Lệnh Master: Tự động phân luồng theo Hệ điều hành"""
    check_env()
    generate_env_dart()

    if platform.system() == "Windows":
        build_windows()
    else:
        build_backend()
        chunk_backend()
        build_ui()

def main():
    parser = argparse.ArgumentParser(description="Sport Seeker CLI Tool")
    parser.add_argument("command", choices=[
        "env", "build-backend", "chunk", "collect-models", "chunk-models",
        "build-ui", "build", "kill", "clean", "pre-commit"
    ], help="Lệnh cần thực thi")

    args = parser.parse_args()

    if args.command == "env":
        check_env()
        generate_env_dart()
    elif args.command == "build-backend":
        check_env()
        build_backend()
    elif args.command == "chunk":
        chunk_backend()
    elif args.command == "collect-models":
        check_env()
        collect_models()
    elif args.command == "chunk-models":
        check_env()
        chunk_models()
    elif args.command == "build-ui":
        check_env()
        generate_env_dart()
        if platform.system() == "Windows":
            build_windows()
        else:
            build_ui()
    elif args.command == "build":
        build_all()
    elif args.command == "kill":
        kill_backend()
    elif args.command == "clean":
        clean_all()
    elif args.command == "pre-commit":
        pre_commit()

if __name__ == "__main__":
    main()
