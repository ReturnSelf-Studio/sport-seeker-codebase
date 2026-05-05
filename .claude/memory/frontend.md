# Frontend (Flutter)

## WorkspaceActions

`ChangeNotifier` + `WidgetsBindingObserver`. Khởi tạo trong `initState` của `WorkspacePage`.

### Lifecycle

- `didChangeAppLifecycleState(resumed)` → `_syncStatusFromBackend()` + reconnect WS nếu null
- `_syncStatusFromBackend()`: GET `/process/status` → sync `isProcessingNotifier` với backend thực tế
- Tránh lệch state khi user Alt+Tab hoặc app bị suspend

### WebSocket

- Auto-reconnect sau 3s nếu drop (`_scheduleReconnect`)
- `onDone` + `onError` đều trigger reconnect
- Không có reconnect → không có lifecycle sync → root cause bug "no data after detect"

### Log handling

- Dòng bắt đầu bằng `   ▶ ` (3 spaces + ▶ + space) = **progress line**
- Progress line không append vào log list — chỉ parse `X/Y frames (Z%)` → `videoProgressText`
- Mọi dòng khác → append bình thường (max 200 dòng)

### Weighted progress

```
progress = (_completedFrames + _currentVideoProcessedFrames) / _totalFrames
```

- `_totalFrames`: tính lúc `startProcess()` từ `prescanData['videos'][*]['total_frames']`
- `_currentVideoProcessedFrames`: parse từ log `   ▶ fname: X/Y frames`
- `_completedFrames` += `total_frames` khi nhận `video_done` event
- Event `progress` từ backend bị **ignore** — tránh override weighted logic

### Prescan flow

1. `loadPrescan()` gọi ngay khi `WorkspacePage` init
2. Hiển thị `WorkspacePrescanWidget` — summary chips + expandable table
3. User bấm "Quét X video chưa quét" hoặc "Quét lại tất cả"
4. `startProcess()` validate: prescanDone, không overLimit, có pending
5. Khi nhận `video_done` → `_applyVideoDone()` update in-memory prescanData realtime
6. Khi nhận `stage: done/stopped` → `loadPrescan()` reload từ backend

## WorkspacePage

- `AutomaticKeepAliveClientMixin` — giữ state khi switch tab
- `WindowListener.onWindowClose()` — intercept close button khi đang processing
- Close dialog: 3 lựa chọn — "Tiếp tục chờ" / "Thu nhỏ" / "Hủy & Thoát"
- "Hủy & Thoát" → `cancelAndRollback()` → `windowManager.destroy()`

## WorkspacePrescanWidget

- Default: summary chips (Tổng/Đã quét/Chưa quét) + action buttons
- "Xem chi tiết" expand table với tên file, thời lượng, trạng thái
- Realtime update khi `video_done` event arrive (không cần reload)
