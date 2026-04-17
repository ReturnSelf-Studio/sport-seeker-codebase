# Sport Seeker - Desktop App 🏃‍♂️🚀

Sport Seeker là ứng dụng Desktop hỗ trợ nhận diện khuôn mặt và trích xuất số BIB của vận động viên từ hình ảnh và video. Ứng dụng được thiết kế theo kiến trúc **Local Microservice**, bao gồm:
* **Frontend:** Flutter Desktop (macOS & Windows).
* **Backend:** Python FastAPI (AI Engine tích hợp InsightFace, PaddleOCR, FAISS).
* **Cơ chế cập nhật (OTA Update):** Tự động tải và áp dụng các bản cập nhật AI Models và Backend thông qua GitHub Raw.

---

## 🛠 Yêu cầu hệ thống (Prerequisites)
Để phát triển và đóng gói dự án, máy tính của bạn cần cài đặt:
1. **Python 3.11+** (Bắt buộc).
2. **Flutter SDK** (Phiên bản 3.19 trở lên).
3. **Git** (Dùng cho quá trình pre-commit và tracking).

*(Lưu ý: Công cụ quản lý package Python `uv` sẽ được script tự động tải và cài đặt nếu chưa có).*

---

## 🚀 Công cụ Quản lý Dự án (CLI Tool)
Toàn bộ quy trình từ thiết lập môi trường, đóng gói (build), đến dọn dẹp hệ thống đều được tự động hóa thông qua công cụ CLI tích hợp sẵn.

Tùy vào hệ điều hành, hãy mở Terminal (hoặc CMD/PowerShell) ở thư mục gốc dự án và sử dụng script tương ứng:
* **Windows:** `scripts\manage.bat <command>`
* **macOS/Linux:** `bash scripts/manage.sh <command>`

### 📜 Danh sách các lệnh (Commands)

| Lệnh | Chức năng |
| :--- | :--- |
| `env` | Kiểm tra file `.env` gốc và tự động sinh file cấu hình `env.dart` cho Flutter. |
| `build-backend` | Đóng gói mã nguồn Python thành file thực thi (Executable) bằng PyInstaller và nén thành `api_payload.zip`. |
| `chunk` | Cắt nhỏ file `api_payload.zip` thành các file 25MB (chunks) vào thư mục `release_data/` để phục vụ OTA Update. |
| `collect-models` | Quét hệ thống (System Cache, Project Root) để thu thập các model AI (InsightFace, PaddleOCR, HuggingFace) và nén thành `offline_models_payload.zip`. |
| `chunk-models` | Cắt nhỏ file Models Zip thành các file 25MB vào thư mục `release_models/`. |
| `build-ui` | Tự động sinh `env.dart`, biên dịch Flutter App thành bản Release và đóng gói thành file ZIP sẵn sàng giao cho khách hàng. |
| `build` | **Lệnh gom (All-in-one):** Chạy tuần tự `env` -> `build-backend` -> `chunk` -> `build-ui`. |
| `kill` | Ép dừng toàn bộ các tiến trình AI ngầm (SportSeekerAPI) đang chạy trên máy tính. |
| `clean` | Dọn dẹp môi trường DEV: Xóa toàn bộ cache models cũ, xóa thư mục ứng dụng trong AppData/Application Support và tắt các tiến trình ngầm. |
| `pre-commit` | Tự động hóa luồng Release: Kiểm tra cấu hình, đóng gói Backend, check mã băm SHA256 của Model để quyết định có cắt nhỏ hay không, sau đó `git add` để chuẩn bị commit. |

---

## 💻 Hướng dẫn Phát triển (Development Workflow)

### 1. Cấu hình môi trường
Tạo file `.env` ở thư mục gốc dự án (nếu chưa có) và cấu hình đường dẫn cập nhật OTA:
```env
BACKEND_UPDATE_URL="https://raw.githubusercontent.com/<User>/<Repo>/main/release_data/"
MODELS_UPDATE_URL="https://raw.githubusercontent.com/<User>/<Repo>/main/release_models/"
```
Đồng bộ cấu hình `.env` vào code Flutter:
```bash
bash scripts/manage.sh env
```

### 2. Chạy thử Backend và UI
* **Chạy AI Engine (Backend):** 
```bash
uv venv --python 3.11
source .venv/bin/activate    # Hoặc .venv\Scripts\activate.bat trên Windows
uv pip install -r requirements-macos-arm64.txt # Hoặc requirements-windows.txt
python main.py
```
* **Chạy Flutter UI:** Mở thư mục `flutter_ui`, gõ lệnh `flutter run` (chọn nền tảng macOS hoặc Windows).

---

## 📦 Hướng dẫn Đóng gói và Phát hành (Release Workflow)

### Cách 1: Đóng gói thủ công toàn bộ ứng dụng
Khi bạn muốn tạo ra một bản cài đặt hoàn chỉnh (File ZIP) để gửi trực tiếp cho khách hàng:
```bash
# Trên Windows
scripts\manage.bat build

# Trên macOS
bash scripts/manage.sh build
```
*Kết quả:* Hệ thống sẽ tạo ra file `SportSeeker_Windows.zip` hoặc `SportSeeker_macOS.zip` ở thư mục gốc. Bạn có thể gửi file này cho khách hàng (Bên trong đã đính kèm sẵn PDF Hướng dẫn cài đặt).

### Cách 2: Phát hành bản cập nhật qua mạng (OTA Update)
Khi bạn chỉ cập nhật code Python hoặc cập nhật AI Model, bạn không cần bắt người dùng cài lại toàn bộ App. Hãy phát hành OTA qua GitHub:

1. Chỉnh sửa file `release_info.json` (tăng số phiên bản).
2. Chạy lệnh tự động hóa:
```bash
bash scripts/manage.sh pre-commit
```
3. Script sẽ tự động đóng gói, chia nhỏ (chunk) và đưa các thay đổi vào Git staging. Việc của bạn chỉ là commit và push lên GitHub:
```bash
git commit -m "chore: release update v1.0.1"
git push origin main
```
*Kết quả:* Các thiết bị của người dùng khi mở ứng dụng sẽ tự động tải các file Chunk từ GitHub Raw về và áp dụng bản cập nhật ngầm.

---

## 🧹 Xử lý sự cố (Troubleshooting)

* **Ứng dụng bị treo không nhận diện được video?**
  Luồng AI có thể bị kẹt trong background. Hãy chạy lệnh:
  `bash scripts/manage.sh kill` (hoặc mở ứng dụng, vào tab *Cài đặt Hệ thống* -> bấm *Force Kill*).
* **Muốn test lại luồng tải AI Models từ đầu như một máy khách hàng mới?**
  Hãy xóa sạch dữ liệu cache bằng lệnh:
  `bash scripts/manage.sh clean`

*** *Document generated for Sport Seeker v1.0.4*