# SPORT SEEKER
## Hướng dẫn cài đặt – macOS (Apple Silicon)

Sport Seeker là ứng dụng nhận diện khuôn mặt và số BIB chạy hoàn toàn offline (Local AI Microservice). Vì ứng dụng dùng nội bộ và không phân phối qua App Store, bộ cài đặt sẽ tự động bypass Gatekeeper thông qua Ad-hoc Code Signing – không cần tài khoản Apple Developer.

---

## Yêu cầu hệ thống

- **macOS:** 12 Monterey trở lên (tối ưu cho Apple Silicon M1/M2/M3/M4)
- **Mạng:** Kết nối Internet cho lần khởi chạy đầu tiên (tải PaddleOCR models ~500MB)
- **Quyền sudo** (mật khẩu tài khoản Mac) để cài đặt vào `/Applications`

---

## Các bước cài đặt

### Bước 1 – Giải nén file tải về

Tải file `SportSeeker_macOS.zip` và giải nén. Thư mục `SportSeeker_macOS` sẽ chứa 2 file:

- `install_sport_seeker.command`
- `sport_seeker` (app bundle)

---

### Bước 2 – Cấp quyền thực thi cho file .command

Trước khi chạy script, cần cấp quyền thực thi cho file `install_sport_seeker.command`. Thực hiện theo các bước sau:

1. Nhấn **Command + Space**, gõ `Terminal` rồi nhấn **Enter** để mở Terminal app.
2. Trong cửa sổ Terminal, gõ lệnh `chmod +x` rồi **kéo thả** file `install_sport_seeker.command` vào Terminal (đường dẫn sẽ tự điền chính xác). Nhấn **Enter**, sau đó nhập mật khẩu Mac khi được yêu cầu và nhấn **Enter**.
3. Sau khi lệnh hoàn tất, file đã sẵn sàng để thực thi. Tiếp tục Bước 3.

---

### Bước 3 – Chạy script cài đặt

**Ctrl + click** (hoặc click chuột phải) vào file `install_sport_seeker.command` → chọn **Open With** → **Terminal**.

Terminal sẽ mở ra và chạy script tự động. Nhập mật khẩu Mac khi được yêu cầu (con trỏ sẽ không hiển thị ký tự – gõ xong bấm **Enter**).

---

### Bước 4 – Chờ cài đặt hoàn tất

Script sẽ tự động thực hiện 4 bước:

1. Copy app vào `/Applications`
2. Gỡ quarantine flag
3. Cấp quyền thực thi
4. Ký Ad-hoc Code Signing

Khi thấy thông báo **"CAI DAT HOAN TAT!"** và app tự khởi động, bấm **Terminate** để đóng Terminal.

---

### Bước 5 – Mở ứng dụng

App `sport_seeker` đã có trong `/Applications` và tìm được qua Spotlight. Mở app bình thường như các ứng dụng khác.

---

## Lưu ý lần khởi chạy đầu tiên

- App sẽ mất **1–3 phút** ở màn hình khởi động để tải PaddleOCR models về `~/.paddlex/` – cần có mạng.
- Các lần mở sau sẽ nhanh hơn và có thể chạy hoàn toàn **offline**.
- Nếu app không mở được sau cài đặt, thử chạy lại script một lần nữa.

---

*Sport Seeker v1.0.0 · Tài liệu nội bộ – không phân phối bên ngoài*
