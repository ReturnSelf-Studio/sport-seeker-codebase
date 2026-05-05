# /qa — Checklist trước khi giao build cho khách hàng

Chạy lần lượt và report kết quả:

1. **Sync check:** Các file trong `memory/workflow.md#files-cần-sync` đã được copy sang main chưa?
2. **macOS:** Không có thay đổi nào trong PaddleOCR path (`ocr_processor_macos.py`)
3. **Windows workarounds:** Các flag PaddleOCR vẫn được set trước import?
4. **Version:** `version.json` đã bump `build_number` chưa?
5. **Pending tasks:** Kiểm tra `memory/workflow.md#pending` còn gì chưa làm?
