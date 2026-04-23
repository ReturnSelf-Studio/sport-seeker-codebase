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
SOURCE_APP="$DIR/Sport Seeker.app"
TARGET_APP="/Applications/Sport Seeker.app"

# Thư mục log dùng chung cho cả runtime và install
LOG_DIR="$HOME/SportSeeker/logs"
mkdir -p "$LOG_DIR"
INSTALL_LOG="$LOG_DIR/install.log"
XATTR_LOG="$LOG_DIR/install_xattr.log"
CODESIGN_LOG="$LOG_DIR/install_codesign.log"

# Reset log install mỗi lần chạy
echo "=== Install $(date '+%Y-%m-%d %H:%M:%S') ===" > "$INSTALL_LOG"

# 2. CHECK VỊ TRÍ ỨNG DỤNG
if [ ! -d "$SOURCE_APP" ]; then
    if [ -d "$TARGET_APP" ]; then
        echo "✅ Đã tìm thấy ứng dụng trong thư mục Applications, tiến hành cấp quyền..."
        echo "INFO: SOURCE_APP not found, using existing TARGET_APP" >> "$INSTALL_LOG"
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

    # [1] Kill tiến trình cũ
    echo "⏳ [1/6] Đang tắt các phiên bản cũ (nếu có)..."
    pkill -9 -f "Sport Seeker" 2>/dev/null || true
    pkill -9 -f "SportSeekerAPI" 2>/dev/null || true
    sleep 1

    # [2] Xóa engine cũ
    # Tìm sport_seeker_backend trong Application Support (không hardcode bundle ID)
    echo "⏳ [2/6] Xóa AI Engine cũ (giữ nguyên Models & dữ liệu người dùng)..."
    ENGINE_FOUND=0
    while IFS= read -r -d '' engine_dir; do
        if [ -d "$engine_dir" ]; then
            rm -rf "$engine_dir"
            echo "   → Đã xóa engine cũ tại: $engine_dir"
            echo "INFO: Removed engine dir: $engine_dir" >> "$INSTALL_LOG"
            ENGINE_FOUND=1
        fi
    done < <(find "$HOME/Library/Application Support" -maxdepth 2 -type d -name "sport_seeker_backend" -print0 2>/dev/null)

    if [ $ENGINE_FOUND -eq 0 ]; then
        echo "   → Không tìm thấy engine cũ (cài lần đầu)."
    fi

    # Reset SharedPreferences: xóa các key version của engine
    echo "   → Đặt lại trạng thái cài đặt engine..."
    PLIST_DIR="$HOME/Library/Preferences"
    PLIST_FOUND=0
    for plist in "$PLIST_DIR"/com.aibus*.plist; do
        if [ -f "$plist" ]; then
            /usr/libexec/PlistBuddy -c "Delete :flutter.installed_engine_version"  "$plist" 2>/dev/null || true
            /usr/libexec/PlistBuddy -c "Delete :flutter.extracted_bundled_version" "$plist" 2>/dev/null || true
            /usr/libexec/PlistBuddy -c "Delete :flutter.installed_backend_version" "$plist" 2>/dev/null || true
            echo "   → Đã reset prefs: $(basename "$plist")"
            echo "INFO: Reset prefs: $plist" >> "$INSTALL_LOG"
            PLIST_FOUND=1
        fi
    done
    if [ $PLIST_FOUND -eq 0 ]; then
        echo "   → Không tìm thấy prefs cũ (cài lần đầu)."
    fi

    # [3] Dọn runtime logs cũ — giữ lại install_*.log để debug
    echo "⏳ [3/6] Dọn dẹp runtime logs cũ..."
    find "$LOG_DIR" -maxdepth 1 -name "*.log" \
        ! -name "install*.log" \
        ! -name "install_xattr.log" \
        ! -name "install_codesign.log" \
        -delete 2>/dev/null || true
    rm -f "$LOG_DIR/checkpoints.log" 2>/dev/null || true
    echo "   → Đã dọn runtime logs."

    # [4] Cài đặt app
    echo "⏳ [4/6] Đang cài đặt ứng dụng vào Applications..."
    sudo rm -rf "$TARGET_APP"
    sudo cp -a "$SOURCE_APP" "/Applications/"
    sudo chown -R "$USER":admin "$TARGET_APP"
    echo "INFO: App installed to $TARGET_APP" >> "$INSTALL_LOG"
fi

# [5] Gỡ quarantine & cấp quyền
echo "⏳ [5/6] Đang gỡ bỏ mác cách ly & cấp quyền thực thi..."
echo "=== xattr log $(date '+%Y-%m-%d %H:%M:%S') ===" > "$XATTR_LOG"

XATTR_SKIP=0
while IFS= read -r -d '' f; do
    if ! sudo xattr -d com.apple.quarantine "$f" 2>/dev/null; then
        # Chỉ log file thực sự có quarantine attribute bị lỗi
        if sudo xattr "$f" 2>/dev/null | grep -q "quarantine"; then
            echo "SKIP: $f" >> "$XATTR_LOG"
            XATTR_SKIP=$((XATTR_SKIP + 1))
        fi
    fi
done < <(find "$TARGET_APP" -print0)

if [ $XATTR_SKIP -gt 0 ]; then
    echo "   ⚠️ $XATTR_SKIP file không gỡ được quarantine — xem log: $XATTR_LOG"
else
    echo "   ✅ Gỡ quarantine OK"
fi

sudo chmod -R +x "$TARGET_APP/Contents/MacOS/"
sudo chmod -R +x "$TARGET_APP/Contents/Frameworks/App.framework/Resources/flutter_assets/assets/backend/"

# [6] Codesign
echo "⏳ [6/6] Đang ký lại ứng dụng (Ad-hoc Codesign)..."
echo "=== codesign log $(date '+%Y-%m-%d %H:%M:%S') ===" > "$CODESIGN_LOG"

sudo codesign --force \
    --preserve-metadata=identifier,entitlements,requirements \
    --sign - \
    "$TARGET_APP/Contents/Frameworks/FlutterMacOS.framework" \
    >> "$CODESIGN_LOG" 2>&1
CODESIGN_FLUTTER=$?
if [ $CODESIGN_FLUTTER -ne 0 ]; then
    echo "   ⚠️ FlutterMacOS.framework: ký không thành công (xem: $CODESIGN_LOG)"
else
    echo "   ✅ FlutterMacOS.framework OK"
fi

sudo codesign --force --deep \
    --preserve-metadata=identifier,entitlements,requirements \
    --sign - \
    "$TARGET_APP" \
    >> "$CODESIGN_LOG" 2>&1
CODESIGN_APP=$?
if [ $CODESIGN_APP -ne 0 ]; then
    echo "   ⚠️ App bundle: ký không thành công (xem: $CODESIGN_LOG)"
else
    echo "   ✅ App bundle OK"
fi

echo "INFO: codesign flutter=$CODESIGN_FLUTTER app=$CODESIGN_APP" >> "$INSTALL_LOG"

echo ""
echo "✅ CÀI ĐẶT HOÀN TẤT!"
echo "🎉 Đang khởi động Sport Seeker..."
echo "   (AI Engine sẽ được cài đặt tự động trong lần chạy đầu tiên)"
if [ $XATTR_SKIP -gt 0 ] || [ $CODESIGN_FLUTTER -ne 0 ] || [ $CODESIGN_APP -ne 0 ]; then
    echo "   📋 Có cảnh báo trong quá trình cài đặt — log tại: $LOG_DIR"
fi
echo "==================================================="

# 4. TỰ ĐỘNG MỞ APP
open "$TARGET_APP"

sleep 2
osascript -e 'tell application "Terminal" to close front window'
