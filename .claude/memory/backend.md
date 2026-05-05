# Backend

## Video pipeline flow

1. `GET /process/prescan/{project_id}` → scan source_dir, build/update manifest, trả summary + video list kèm `total_frames`
2. `POST /process/start` → backup index, tạo asyncio task `run_processing()`
3. `run_processing()` → sort files (ảnh nhỏ→lớn, video nhỏ→lớn), loop qua từng file
4. `_process_single_video()` → 3 threads (read/detect/save), emit log `   ▶ fname: X/Y frames (Z%)` mỗi 2s
5. Sau mỗi video xong: `vs.save()` → `manifest.mark_done()` → emit `video_done` WS event
6. Nếu stop: `manifest.mark_failed()`, không save
7. Cuối session: emit `stage: done`, `clear_backup()`

## WebSocket events (backend → frontend)

| Event type | Data | Ý nghĩa |
|------------|------|---------|
| `log` | `string` | Static log hoặc progress line (prefix `   ▶ `) |
| `stage` | `init/ready/done/error/stopped` | Trạng thái task |
| `video_done` | `{name, total_frames}` | Một video hoàn tất |

> Event `progress` vẫn được emit nhưng frontend ignore — không dùng để tính progress bar.

## VideoManifest

- Key = **tên file** (không phải path) — đổi tên = video mới, quét lại
- `scan_status`: `no-scan` / `scanning` / `done`
- `scanning` bị reset về `no-scan` khi prescan (crash recovery)
- `total_frames` được đọc qua OpenCV khi video lần đầu xuất hiện, backfill cho video cũ

## Index backup/restore

- `backup_index()` gọi trước `start` — chỉ backup nếu index folder có file
- `restore_index()` gọi khi user cancel — nếu không có backup thì xóa index hiện tại
- `clear_backup()` gọi sau `done` thành công

## Rollback cancel

`POST /process/cancel`:
1. Set `processing_stop_flag = True`
2. Chờ task dừng (timeout 10s)
3. `restore_index()` — khôi phục index về trước session
4. `manifest.reset_all_scanning()` — reset video đang dở về `no-scan`

## Search

- Bị block nếu task đang chạy (HTTP 400)
- `apply_index_paths()` trước khi tạo `VectorStore` — đảm bảo đọc đúng project
