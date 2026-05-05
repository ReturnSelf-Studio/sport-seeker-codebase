# Known Issues & Workarounds

## macOS

- **PaddleOCR Symlink Crash:** Giải nén bằng Dart package / .zip làm hỏng symlink `.dylib` → Fix: dùng `.tar.gz` + native `tar -xzf`
- **imageio OTA bug:** Patch `importlib.metadata.version` để fake `imageio==2.31.0`

## Windows

- **Unicode path (cv2):** Không đọc/ghi path tiếng Việt → `numpy frombuffer` + `imencode`
- **FAISS Unicode:** Write/read qua tempfile ASCII rồi move
- **PaddleOCR flags:** Set trước mọi import: `FLAGS_use_mkldnn=0`, `FLAGS_use_new_executor=0`, `PADDLE_DISABLE_ONEDNN=1`
- **PaddleOCR incompatible (Windows):** Models build trên Linux/Mac chứa `fused_conv2d` OneDNN ops → thay bằng RapidOCR
- **recursionlimit:** Set 100000 cho PaddleOCR/PaddlePaddle

## Backend

- `zombie_killer` thread: auto-exit nếu parent Flutter process chết
- `settings` singleton bị mutate bởi `apply_index_paths()` — không gọi đồng thời từ 2 context
- Search bị block khi task đang chạy (HTTP 400) — tránh đọc index giữa chừng

## Bug đang điều tra — WinError 1114 (máy user `tungn`)

```
WinError 1114: DLL initialization routine failed
Error loading: torch\lib\c10.dll
```

Cần user chạy:
```powershell
Get-ItemProperty HKLM:\SOFTWARE\Microsoft\VisualStudio\*\VC\Runtimes\* 2>$null | Select-Object Version, Installed | Sort-Object Version
cd "C:\Users\tungn\AppData\Roaming\SportSeeker\app\backend"
.venv\Scripts\python.exe -c "import torch; print(torch.__version__)"
.venv\Scripts\python.exe -c "import torch; print(torch.cuda.is_available())"
```

Fix thường gặp: cài lại VC++ Redist 2015-2022 x64, check CUDA version, Windows N/KN cài Media Feature Pack.
