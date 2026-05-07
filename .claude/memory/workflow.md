# Workflow

## Git

- Branch `minimal-codebase` → edit, commit, push tại đây; chỉ giữ code/config tương ứng
- Folder `../sport-seeker-codebase/` → branch `main`, chỉ dùng để nhận file và build/release, không push từ đây
- Remote URL giống nhau, 2 folder riêng biệt trên disk

## Build/release scripts

Không chạy build/debug trong `minimal-codebase`. Nếu cần build/release, sync code/config bằng local devtools sang `../sport-seeker-codebase/`, rồi thao tác ở folder branch `main`.

| Command | Script | Mô tả |
|---------|--------|-------|
| `env` | `scripts/generate_env_dart.py` | Sync .env → lib/core/env.dart |
| `build-backend` | `scripts/cmd_backend.py` | PyInstaller → tar.gz (Mac) / zip (Win) |
| `collect-models` | `scripts/collect_models.py` | Gom models → zip |
| `chunk-models` | — | Cắt zip → 25MB chunks cho release |
| `build-ui` | `scripts/build_ui.py` | gen env.dart + flutter build + bundle |
| `build` | all-in-one | env → build-backend → build-ui |
| `kill` | `scripts/cmd_backend.py kill` | Force kill SportSeekerAPI |
| `clean` | `scripts/clean.bat` | Xóa cache, AppData, kill processes |

## Local DevTools (`.devtools.ps1` / `.dev/`)

- `.devtools.ps1` là PowerShell bootstrap ở root.
- `.dev/` chứa Python DevTools local-only.
- `.devtools.ps1` kiểm tra/cài `uv`, tạo venv tại `.dev/.venv`, rồi ủy thác cho `.dev/main.py`.
- Công cụ này **chỉ dành cho máy dev local**. Không cần và không nên đảm bảo chạy trên Windows/client release.
- `.devtools.ps1` và `.dev/` nằm trong `.gitignore`; không push git.
- `dev_collect.py`: thu thập danh sách file code/config từ folder hiện tại, bỏ local env/build/debug/runtime artifacts.
- `dev_sync.py`: gọi `dev_collect.py`, rồi copy + ghi đè file đã collect sang `../sport-seeker-codebase/`.

## Session notes

- Handoff chi tiết gần nhất: `memory/session_2026-05-05.md`
- Build Windows thực tế đang đi qua `../sport-seeker-codebase/scripts/manage.bat`.
- Nếu Python stdout còn dùng codepage cp1252, build có thể fail vì `UnicodeEncodeError` khi script in icon/Unicode.
- Hướng analytics mới ưu tiên backend-centric thay vì frontend-centric.

## Versioning (`version.json`)

- `increment_build.py`: tự bump `build_number` mỗi build
- Hash toàn bộ Python files trong `app/`, `main.py`, `requirements*`, `pyproject.toml`, `uv.toml` → nếu thay đổi thì bump `backend_version` patch + ghi `backend_source_hash`
- `backend_source_hash` để trống lần đầu — tự fill khi build đầu tiên

## Delivery

| Platform | Release folder | Install script |
|----------|---------------|----------------|
| macOS | `SportSeeker_macOS_Release/` | `scripts/install_sport_seeker.command` |
| Windows | `SportSeeker_Windows_Release/` | `scripts/install_sport_seeker.bat` |

## Pending

- Tích hợp `uninstall_sport_seeker.command` vào `build_ui.py`
- Tích hợp `uninstall_sport_seeker.bat` vào `build_windows.py`

