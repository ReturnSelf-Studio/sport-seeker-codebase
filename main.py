"""
main.py — Sport Seeker Backend Entry Point.
"""
import os
import sys
import multiprocessing

if sys.platform == 'win32' and getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    for extra_path in [base_path, os.path.join(base_path, 'faiss'), os.path.join(base_path, 'numpy.libs')]:
        if os.path.exists(extra_path):
            os.add_dll_directory(extra_path)
            os.environ['PATH'] = extra_path + os.pathsep + os.environ['PATH']

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "TRUE")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import uvicorn
import app.api.server

def main():
    multiprocessing.freeze_support()
    print("[SportSeeker] Starting Backend API on 127.0.0.1:10330...")
    uvicorn.run("app.api.server:app", host="127.0.0.1", port=10330, reload=False)

if __name__ == "__main__":
    main()
