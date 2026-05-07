# Architecture

## Paths

| Path | Role |
|------|------|
| `minimal-codebase/` | Working branch (`minimal-codebase`) — chỉ chứa code/config, edit + push |
| `../sport-seeker-codebase/` | Branch `main` cùng repo — nhận file từ devtools local để build/release |

## Stack

- **Frontend:** Flutter Desktop (macOS Apple Silicon + Windows)
- **Backend:** Python 3.11 FastAPI + uvicorn, chạy local như subprocess của Flutter tại `127.0.0.1:10330`
- **Python package manager:** `uv`
- **macOS OCR:** PaddleOCR (stable, không động vào)
- **Windows OCR:** RapidOCR + onnxruntime-directml
- **AI models:** bundled offline, OTA qua GitHub Raw chỉ cho models (chunked 25MB)
- **Backend delivery:** PyInstaller → `api_payload.tar.gz` (macOS) / source zip (Windows)

## AI Stack

| Component | Tech |
|-----------|------|
| Face recognition | InsightFace buffalo_l via ONNX Runtime |
| OCR (BIB) | PaddleOCR (macOS) / RapidOCR (Windows) |
| Text embedding | SentenceTransformers all-MiniLM-L6-v2 |
| Vector DB | FAISS flat index |
| ONNX providers | CoreML (macOS ARM) → DirectML (Windows GPU) → CPU |

## Backend structure

```
resource/backend/
├── main.py
├── app/
│   ├── api/
│   │   ├── server.py
│   │   └── routers/
│   │       ├── engine.py       # /process/prescan, /start, /stop, /cancel, /status, /search
│   │       ├── projects.py     # CRUD /projects
│   │       └── system.py       # /health, /models/status, /system/storage, /shutdown
│   ├── core/
│   │   ├── config.py           # Settings singleton — ONNX provider, model paths, hyperparams
│   │   ├── face_processor.py   # InsightFace wrapper
│   │   ├── ocr_processor.py    # Platform dispatch → _windows.py hoặc _macos.py
│   │   ├── tracker.py          # Cosine-similarity face tracking across frames
│   │   ├── vector_store.py     # FAISS CRUD, safe_faiss_write/read (Windows Unicode workaround)
│   │   ├── project_manager.py  # CRUD projects, apply_index_paths()
│   │   ├── video_manifest.py   # Per-video scan state, index backup/restore
│   │   └── logger.py           # setup_logging()
│   └── services/
│       ├── ai_engine.py        # Singleton: lazy-load models, model_status, write_checkpoint()
│       ├── video_pipeline.py   # run_processing(), _process_single_video()
│       └── ws_manager.py       # emit_log, emit_progress, emit_stage
└── .venv/                      # managed by uv
```

## Frontend structure

```
frontend/lib/
├── main.dart
├── core/
│   ├── backend_manager.dart           # Abstract interface
│   ├── backend_manager_macos.dart     # Giải nén tar.gz bằng native 'tar -xzf' (giữ symlink)
│   ├── backend_manager_windows.dart   # Launch source backend, manage PID
│   └── model_manager.dart             # OTA model download/update
├── ui/
│   ├── theme.dart                     # Dark theme
│   └── pages/
│       ├── splash_page.dart           # Launch backend → wait /health → navigate
│       ├── project_manager_page.dart
│       ├── workspace_page.dart        # Tab 1: Cấu hình & xử lý, WindowListener close dialog
│       ├── workspace/
│       │   ├── workspace_actions.dart          # ChangeNotifier: WS, lifecycle, prescan, weighted progress
│       │   ├── workspace_prescan_widget.dart   # Summary + expandable table
│       │   └── workspace_control_widget.dart   # Progress bar + status
│       ├── search_page.dart           # Face/BIB search, Empty State thân thiện
│       └── settings_page.dart         # Storage info, force kill backend
```

## Data paths

| Data | Path |
|------|------|
| Models | `~/SportSeeker/models/` |
| Projects registry | `~/SportSeeker/projects/projects.json` |
| Project index | `~/SportSeeker/projects/<name>_<id>/index/` |
| Video manifest | `project_dir/.ss_meta/video_manifest.json` |
| Index backup | `project_dir/.ss_meta/index_backup/` |
| Logs | `~/SportSeeker/logs/checkpoints.log` |
| Engine (macOS) | `~/Library/Application Support/com.aibus.sportSeeker/sport_seeker_backend/` |

## Key design decisions

- `settings` là global singleton — `apply_index_paths()` mutate trực tiếp. Không gọi đồng thời.
- `vs.save()` sau **mỗi video**, không phải cuối session.
- Video sort theo `size_bytes` ascending — nhỏ/ngắn xử lý trước.
- Backend OTA đã bỏ — chỉ còn model OTA.
- Stop/Pause UI đã gỡ khỏi workspace để tránh lỗi logic UX.
- Analytics/tracking được định hướng chuyển về backend để đồng bộ Windows/macOS; frontend không nên là source of truth cho session/device metrics.
