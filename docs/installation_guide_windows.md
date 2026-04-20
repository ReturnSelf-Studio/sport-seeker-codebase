# SPORT SEEKER
## Hướng dẫn cài đặt – Windows (x64)

Sport Seeker là ứng dụng nhận diện khuôn mặt và số BIB chạy nội bộ. Trên nền tảng Windows, ứng dụng sẽ tự động tải và cấu hình môi trường AI một cách an toàn mà không ảnh hưởng đến hệ thống máy tính của bạn.

---

## Yêu cầu hệ thống

- **Hệ điều hành:** Windows 10 hoặc Windows 11 (64-bit)
- **Mạng:** Cần có kết nối Internet ổn định cho lần cài đặt đầu tiên (để hệ thống tự động tải Python và các thư viện AI ~500MB)

---

## Các bước Cài đặt

### Bước 1 – Giải nén file

Sau khi tải file `SportSeeker_Windows.zip` về máy, bạn bắt buộc phải giải nén toàn bộ file ra một thư mục (Click chuột phải vào file ZIP → Chọn **Extract All...**).

> ⚠️ **Không được** click đúp vào file ZIP và chạy trực tiếp từ bên trong – ứng dụng sẽ báo lỗi.

---

### Bước 2 – Chạy công cụ Cài đặt

Vào thư mục vừa giải nén, bạn sẽ thấy file `install_sport_seeker.bat`. Nhấn chuột phải vào vùng trống thư mục → chọn **Open in Terminal**. Sau đó gõ lệnh:

```
.\install_sport_seeker.bat
```

rồi nhấn **Enter**.

---

### Bước 3 – Chờ hệ thống tự động cấu hình

Hệ thống sẽ tự động tải và cài đặt môi trường AI. Quá trình này hiển thị thanh tiến trình màu sắc và mất khoảng **1 đến 3 phút** tùy vào tốc độ mạng. Vui lòng không đóng cửa sổ này.

---

### Bước 4 – Tạo lối tắt (Shortcut)

Khi cài đặt gần xong, hệ thống sẽ hỏi:

> *"Bạn có muốn tạo Shortcut ngoài màn hình Desktop không? (Y/N)"*

Gõ phím **Y** và bấm **Enter** để có icon ngoài màn hình chính. Ứng dụng cũng sẽ tự động thêm vào Start Menu. Khi thấy dòng chữ **"CÀI ĐẶT THÀNH CÔNG!"**, bấm phím bất kỳ để đóng cửa sổ.

---

### Bước 5 – Mở ứng dụng

Ứng dụng đã được cài đặt vào hệ thống. Bạn có thể xóa thư mục giải nén ban đầu cho nhẹ máy. Để mở ứng dụng:

- Click đúp vào icon **Sport Seeker** ngoài Desktop, hoặc
- Bấm phím **Windows** và gõ `Sport Seeker` để tìm kiếm.

---

## Lưu ý lần khởi chạy đầu tiên

- App sẽ mất **1–3 phút** ở màn hình khởi động để tải PaddleOCR models về `~/.paddlex/` – cần có mạng.
- Các lần mở sau sẽ nhanh hơn và có thể chạy hoàn toàn **offline**.
- Nếu Windows Firewall hỏi quyền mạng, chọn **Allow** để cho phép tải models.

---

## Xử lý sự cố (Troubleshooting)

**Script báo lỗi "Không tìm thấy thư mục resource":**
Bạn đang chạy nhầm file `.bat` từ bên trong file ZIP chưa giải nén. Hãy làm lại Bước 1.

**Cài đặt bị dừng quá lâu ở bước 3:**
Hãy kiểm tra lại kết nối mạng của bạn. Nếu lỗi, hãy đóng cửa sổ và chạy lại file `.bat` một lần nữa.

**Bị phần mềm diệt virus (Windows Defender) cảnh báo:**
Do đây là phần mềm nội bộ (không đưa lên Microsoft Store), một số phần mềm diệt virus có thể nhận diện nhầm. Bạn có thể hoàn toàn yên tâm cho phép (**Allow**) để ứng dụng hoạt động bình thường.

---

*Sport Seeker v1.0.0 · Tài liệu nội bộ – không phân phối bên ngoài*
