# Sport Seeker

Flutter Desktop + Python FastAPI — detect face & BIB number từ ảnh/video thể thao.
Local microservice: Flutter frontend ↔ HTTP REST + WebSocket (`127.0.0.1:10330`).

## Quick ref

| Cần biết về | Đọc |
|-------------|-----|
| Cấu trúc project, stack, AI, data paths | `memory/architecture.md` |
| Git workflow, versioning, local devtools | `memory/workflow.md` |
| Backend pipeline, manifest, vector store, WS events | `memory/backend.md` |
| Flutter WS, lifecycle, weighted progress, prescan | `memory/frontend.md` |
| Windows install, OCR, known issues, bugs | `memory/windows.md` |
| Tất cả known issues & workarounds | `memory/known_issues.md` |
| Handoff session gần nhất | `memory/session_2026-05-05.md` |

## Nguyên tắc bất biến

- **Không động macOS pipeline** (PaddleOCR path). Windows dùng RapidOCR.
- **Không push từ `sport-seeker-codebase/` (branch `main`).**
- **Không build/debug từ `minimal-codebase`.**
- Local devtools nằm trong `.dev/` và `.devtools.ps1`, chỉ chạy trên máy dev và không push git.
- Stop/Pause UI đã bị gỡ khỏi workspace — không re-implement.
