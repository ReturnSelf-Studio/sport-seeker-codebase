# scripts/core_utils.py
import subprocess
import sys
import platform

def run_cmd(cmd, cwd=None, capture_output=False, ignore_error=False, quiet=False):
    """
    Hàm chạy lệnh Shell dùng chung cho cả Dev CLI và Client Installer
    """
    if not quiet: 
        print(f"> Running: {cmd}")
        
    # Chuẩn bị tham số cho subprocess
    kwargs = {
        "shell": True,
        "cwd": cwd,
        "text": True
    }
    
    # Nếu đang bật chế độ yên tĩnh (quiet), ép hệ điều hành ngậm miệng (chặn cả stdout và stderr)
    if capture_output:
        kwargs["capture_output"] = True
    elif quiet:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
        
    result = subprocess.run(cmd, **kwargs)
    
    if result.returncode != 0 and not ignore_error:
        if not quiet: 
            error_msg = result.stderr if capture_output else "Check console output."
            print(f"[LỖI] Lệnh thất bại (Code {result.returncode}): {error_msg}")
        sys.exit(result.returncode)
        
    return result

def kill_sport_seeker_processes(os_name=None, quiet=False):
    """
    Hàm ép dừng tiến trình (Backend, Frontend, Port) dùng chung cho Dev và Client
    """
    if os_name is None:
        os_name = platform.system()
        
    if not quiet:
        print("\n🧹 Đang dọn dẹp các tiến trình SportSeeker...")
        
    if os_name == "Windows":
        run_cmd("taskkill /F /IM SportSeekerAPI.exe /T", ignore_error=True, quiet=True)
        run_cmd("taskkill /F /IM sport_seeker.exe /T", ignore_error=True, quiet=True)
        run_cmd('for /f "tokens=5" %a in (\'netstat -aon ^| findstr :10330\') do taskkill /F /PID %a /T', ignore_error=True, quiet=True)
    else:
        run_cmd("pkill -9 -f 'Sport Seeker'", ignore_error=True, quiet=True)
        run_cmd("pkill -9 -f 'SportSeekerAPI'", ignore_error=True, quiet=True)
        run_cmd("lsof -t -i :10330 | xargs kill -9", ignore_error=True, quiet=True)
        
    if not quiet:
        print("✅ Hoàn tất dọn dẹp tiến trình!")

class Logger:
    """Class hỗ trợ ghi log song song ra màn hình và file (cho Installer)"""
    def __init__(self, log_file):
        self.terminal = sys.stdout
        self.log = open(log_file, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        pass
