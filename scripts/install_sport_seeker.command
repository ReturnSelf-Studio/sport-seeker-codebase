#!/bin/bash

clear
echo "==================================================="
echo "     SPORT SEEKER - BỘ CÀI ĐẶT TỰ ĐỘNG (MACOS)"
echo "==================================================="
echo ""

# 1. CHECK HỆ ĐIỀU HÀNH
if [[ "$(uname)" != "Darwin" ]]; then
    echo "❌ LỖI: Script này chỉ dành cho hệ điều hành macOS (Apple)."
    echo "👉 Nếu bạn dùng Windows, vui lòng chạy file cài đặt của Windows."
    echo ""
    read -p "Bấm phím Enter để thoát..."
    exit 1
fi

# Lấy đường dẫn thư mục hiện tại
DIR=$(cd "$(dirname "$0")" && pwd)
# ĐÃ ĐỔI TÊN Ở ĐÂY
SOURCE_APP="$DIR/Sport Seeker.app"
TARGET_APP="/Applications/Sport Seeker.app"

# 2. CHECK VỊ TRÍ ỨNG DỤNG
if [ ! -d "$SOURCE_APP" ]; then
    if [ -d "$TARGET_APP" ]; then
        echo "✅ Đã tìm thấy ứng dụng trong thư mục Applications, tiến hành cấp quyền..."
    else
        echo "❌ LỖI: Không tìm thấy 'Sport Seeker.app'."
        echo "👉 Vui lòng đảm bảo file script này nằm CÙNG MỘT THƯ MỤC với file 'Sport Seeker.app'."
        echo ""
        read -p "Bấm phím Enter để thoát..."
        exit 1
    fi
else
    echo "Hệ thống sẽ yêu cầu mật khẩu máy Mac của bạn để cài đặt."
    echo "(Lưu ý: Khi gõ mật khẩu trên màn hình sẽ KHÔNG HIỆN DẤU ***, cứ gõ rồi bấm Enter)"
    echo ""
    
    echo "⏳ [1/4] Đang tắt các phiên bản cũ (nếu có) và cài đặt ứng dụng..."
    # Cập nhật tên tiến trình pkill
    pkill -9 -f "Sport Seeker" 2>/dev/null || true
    pkill -9 -f "SportSeekerAPI" 2>/dev/null || true
    
    sudo rm -rf "$TARGET_APP"
    sudo cp -R "$SOURCE_APP" "/Applications/"
    sudo chown -R "$USER":admin "$TARGET_APP"
fi

# 3. THỰC THI (Fix Permissions & Codesign)
echo "⏳ [2/4] Đang gỡ bỏ mác cách ly ứng dụng tải từ Internet..."
sudo xattr -rd com.apple.quarantine "$TARGET_APP" || echo "⚠️ Bỏ qua bước mác cách ly..."

echo "⏳ [3/4] Đang cấp quyền thực thi cho ứng dụng..."
sudo chmod -R +x "$TARGET_APP/Contents/MacOS/"
sudo chmod -R +x "$TARGET_APP/Contents/Frameworks/App.framework/Resources/flutter_assets/assets/backend/"

echo "⏳ [4/4] Đang ký lại ứng dụng (Ad-hoc Codesign)..."
sudo codesign --force --deep --preserve-metadata=identifier,entitlements,requirements --sign - "$TARGET_APP"

echo ""
echo "✅ CÀI ĐẶT HOÀN TẤT!"
echo "🎉 Đang khởi động Sport Seeker..."
echo "==================================================="

# 4. TỰ ĐỘNG MỞ APP
open "$TARGET_APP"

sleep 2
osascript -e 'tell application "Terminal" to close front window'
