# Windows

## Install pipeline (`install_sport_seeker.bat`)

- **Steps 1–2:** VC++ Redist + MSVC Build Tools — chạy qua elevated admin window với pause-and-rerun loop
- Flow này **không được phá vỡ** — user phải confirm từng bước
- `$env:TEMP` không expand trong temp batch files → dùng `%TEMP%`
- PowerShell 5 không support `&&` trong `-ArgumentList` → viết temp `.bat`
- `uv pip install` cần flag `--python venv_python`
- `uv.toml` phải nằm trong `resource/backend/` để `only-binary` constraints áp dụng

## OCR

- Windows dùng **RapidOCR + onnxruntime-directml** thay PaddleOCR
- Lý do: PaddleOCR models build trên Linux/Mac chứa `fused_conv2d` OneDNN ops — incompatible trên Windows
- `get_available_providers()` tự chọn GPU/CPU
- **Không dùng PaddleOCR trên Windows**

## Flutter launch backend

```
.venv\Scripts\python.exe  (trong backend dir)
```

## Bug đang điều tra — WinError 1114

**Máy:** user `tungn`
**Lỗi:** `WinError 1114: DLL initialization routine failed. Error loading torch\lib\c10.dll`
**Nghi ngờ:** Visual C++ Redistributable thiếu hoặc sai version

**Cần user chạy:**
```powershell
# Check VC++ Redist
Get-ItemProperty HKLM:\SOFTWARE\Microsoft\VisualStudio\*\VC\Runtimes\* 2>$null | Select-Object Version, Installed | Sort-Object Version

# Check torch load
cd "C:\Users\tungn\AppData\Roaming\SportSeeker\app\backend"
.venv\Scripts\python.exe -c "import torch; print(torch.__version__)"
.venv\Scripts\python.exe -c "import torch; print(torch.cuda.is_available())"
```

**Fix thường gặp:**
1. Cài lại VC++ Redist 2015-2022 x64 từ Microsoft
2. Nếu máy có GPU: kiểm tra CUDA version khớp với torch build
3. Nếu Windows N/KN: cài Media Feature Pack

## Known workarounds (từ handoff.json)

- **Unicode path:** `cv2` không đọc/ghi path tiếng Việt → dùng `numpy frombuffer` + `imencode`
- **FAISS Unicode:** write/read qua tempfile ASCII rồi move
- **PaddleOCR Windows:** set `FLAGS_use_mkldnn=0`, `FLAGS_use_new_executor=0`, `PADDLE_DISABLE_ONEDNN=1` **trước** mọi import
- **recursionlimit:** set 100000 cho PaddleOCR/PaddlePaddle
