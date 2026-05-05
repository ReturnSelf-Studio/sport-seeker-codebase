# Workflow

## Git

- Branch `minimal-codebase` → edit, commit, push tại đây
- Branch `main` → chỉ dùng để build, không push
- Remote URL giống nhau, 2 folder riêng biệt trên disk

## Sync trước khi build

```bash
bash .claude/sync.sh
```

## Build scripts

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

## Local DevTools (`.devtools` / `.dev/`)

- `.devtools` là **file shell script ở root**, không phải folder.
- `.dev/` chứa Python DevTools local-only: `tree`, `collect`, `zip`, `save`, `load`, `sync`.
- `.devtools` bootstrap `.dev/.venv`, tìm/cài `uv`, rồi chạy `.dev/main.py`.
- Công cụ này **chỉ dành cho máy dev local**. Không cần và không nên đảm bảo chạy trên Windows/client release.
- Việc `.devtools` trong session macOS/Linux không chạy được trên Windows là chủ đích đúng: đây là tooling cá nhân để hỗ trợ sync/build workflow, không phải runtime app.
- `.devtools` và `.dev/` nằm trong `.gitignore`; nếu cần copy sang `codebase-main` chỉ dùng flag chủ động: `./.devtools sync --include-devtools`.

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

## Files cần sync (danh sách hiện tại)

**Backend:**
- `resource/backend/app/core/video_manifest.py`
- `resource/backend/app/core/project_manager.py`
- `resource/backend/app/api/routers/engine.py`
- `resource/backend/app/services/video_pipeline.py`

**Frontend:**
- `lib/ui/pages/workspace_page.dart`
- `lib/ui/pages/workspace/workspace_actions.dart`
- `lib/ui/pages/workspace/workspace_prescan_widget.dart`
- `lib/ui/pages/workspace/workspace_control_widget.dart`
