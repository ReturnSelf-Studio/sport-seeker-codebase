# Hướng dẫn Cài đặt Sport Seeker (Windows)

Tài liệu này hướng dẫn chi tiết các bước để cài đặt và khởi chạy ứng dụng Sport Seeker trên hệ điều hành Windows 10 và Windows 11.

---

## Yêu cầu Hệ thống
* **Hệ điều hành:** Windows 10 hoặc Windows 11 (64-bit).
* **Dung lượng trống:** Tối thiểu 2GB.
* **Kết nối Internet:** Cần thiết trong quá trình cài đặt để tải các thành phần bổ trợ.

---

## Các bước Cài đặt

### Bước 1 – Giải nén gói cài đặt
1. Tìm file **SportSeeker_Windows.zip** bạn đã tải về.
2. Nhấn chuột phải vào file và chọn **Extract All...** (Giải nén tất cả).
3. Chọn thư mục lưu trữ và nhấn **Extract**. 
   *Lưu ý: Không chạy file cài đặt trực tiếp từ bên trong file Zip.*

### Bước 2 – Thực hiện Cài đặt hệ thống
Vào thư mục vừa giải nén, tìm file **install_sport_seeker.bat** và thực hiện theo các bước sau:

1. **Khởi chạy:** Nhấp đúp chuột (double-click) vào file **install_sport_seeker.bat**.
2. **Xác nhận bảo mật:** Nếu xuất hiện cửa sổ cảnh báo "Windows protected your PC", hãy nhấn vào dòng chữ **More info** (Thông tin thêm), sau đó chọn **Run anyway** (Vẫn chạy).
3. **Cài đặt thành phần bổ trợ (C++ Build Tools):** Tại bước 2/4 của tiến trình, hệ thống sẽ kiểm tra thư viện Microsoft C++ Build Tools.
   - Nếu máy tính chưa có thành phần này, một thông báo **User Account Control (UAC)** sẽ yêu cầu quyền quản trị. Vui lòng chọn **Yes**.
   - Một cửa sổ dòng lệnh mới sẽ xuất hiện để tự động cài đặt Build Tools. Hãy chờ khoảng **15-30 giây** cho đến khi tiến trình hoàn tất, sau đó **đóng cửa sổ phụ này** để quay lại màn hình chính.
4. **Tiếp tục tiến trình:**
   - **Đối với Windows 11:** Thông thường tiến trình sẽ tự động tiếp tục các bước 3 và 4.
   - **Đối với Windows 10 (hoặc nếu tiến trình bị dừng):** Nếu cửa sổ Terminal ban đầu hiện thông báo "Press any key to exit" hoặc tự đóng lại, bạn chỉ cần **nhấp đúp chuột vào file install_sport_seeker.bat một lần nữa**. Hệ thống sẽ tự động bỏ qua các bước đã xong và hoàn tất phần còn lại.
5. **Hoàn tất:** Khi màn hình hiển thị thông báo cài đặt thành công, bạn có thể đóng Terminal.

### Bước 3 – Khởi chạy ứng dụng
Sau khi cài đặt thành công, bạn có thể mở ứng dụng bằng hai cách:
* Tìm biểu tượng **Sport Seeker** trên màn hình Desktop.
* Hoặc tìm kiếm ứng dụng trong **Start Menu**.

---

## Lưu ý cho lần khởi chạy đầu tiên
Trong lần đầu tiên sử dụng tính năng tìm kiếm AI hoặc quét khuôn mặt, ứng dụng sẽ tự động tải các mô hình trí tuệ nhân tạo (AI Models) từ máy chủ.
* **Thời gian tải:** Tùy thuộc vào tốc độ mạng (khoảng 3-5 phút).
* **Tiến độ:** Bạn có thể theo dõi thanh phần trăm (%) hiển thị ngay trên ứng dụng.
* **Thư mục lưu trữ:** Các mô hình này sẽ được lưu tại đường dẫn `C:\Users\<Tên_User>\.paddleocr` và `~/.insightface`. Vui lòng không xóa các thư mục này để đảm bảo tốc độ khởi động cho những lần sau.

---

## Xử lý sự cố (Troubleshooting)

**1. Lỗi "Unknown Publisher" hoặc không cho chạy file .bat:**
Đây là cơ chế bảo vệ mặc định của Windows đối với ứng dụng nội bộ. Hãy thực hiện đúng như hướng dẫn tại **Bước 2.2** (More info -> Run anyway).

**2. Ứng dụng không khởi động được AI Engine:**
Vui lòng kiểm tra xem Windows Firewall (Tường lửa) hoặc phần mềm diệt virus có đang chặn ứng dụng hay không. Hãy chọn **Allow Access** nếu có thông báo yêu cầu truy cập mạng.

**3. Tiến trình cài đặt bị treo ở bước tải dữ liệu:**
Hãy kiểm tra kết nối Internet của bạn. Bạn có thể tắt cửa sổ Terminal và chạy lại file **install_sport_seeker.bat** để hệ thống tiếp tục tải lại những phần còn thiếu.