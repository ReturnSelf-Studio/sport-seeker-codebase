#!/bin/bash

clear
echo "==================================================="
echo "     SPORT SEEKER - GỠ CÀI ĐẶT (MACOS)"
echo "==================================================="
echo ""
echo "⚠️  CẢNH BÁO: Thao tác này sẽ xóa TOÀN BỘ dữ liệu của Sport Seeker,"
echo "    bao gồm:"
echo "    - Ứng dụng Sport Seeker"
echo "    - AI Engine (backend)"
echo "    - AI Models đã tải về"
echo "    - Toàn bộ dữ liệu dự án và kết quả xử lý"
echo "    - Logs"
echo ""
echo "    Thao tác này KHÔNG THỂ HOÀN TÁC."
echo ""
read -p "Bạn có chắc chắn muốn gỡ cài đặt? Gõ 'XOA' để xác nhận: " CONFIRM

if [ "$CONFIRM" != "XOA" ]; then
    echo ""
    echo "❌ Đã hủy. Không có gì bị xóa."
    sleep 2
    exit 0
fi

echo ""
echo "⏳ [1/6] Đang tắt tiến trình Sport Seeker..."
pkill -9 -f "Sport Seeker" 2>/dev/null || true
pkill -9 -f "SportSeekerAPI" 2>/dev/null || true
sleep 1
echo "   ✅ Xong."

echo "⏳ [2/6] Đang xóa ứng dụng khỏi Applications..."
TARGET_APP="/Applications/Sport Seeker.app"
if [ -d "$TARGET_APP" ]; then
    sudo rm -rf "$TARGET_APP"
    echo "   ✅ Đã xóa: $TARGET_APP"
else
    echo "   → Không tìm thấy app trong Applications, bỏ qua."
fi

echo "⏳ [3/6] Đang xóa AI Engine..."
while IFS= read -r -d '' engine_dir; do
    rm -rf "$engine_dir"
    echo "   ✅ Đã xóa engine: $engine_dir"
done < <(find "$HOME/Library/Application Support" -maxdepth 2 -type d -name "sport_seeker_backend" -print0 2>/dev/null)

echo "⏳ [4/6] Đang xóa dữ liệu ứng dụng (models, projects, logs)..."
SPORT_SEEKER_DIR="$HOME/SportSeeker"
if [ -d "$SPORT_SEEKER_DIR" ]; then
    rm -rf "$SPORT_SEEKER_DIR"
    echo "   ✅ Đã xóa: $SPORT_SEEKER_DIR"
else
    echo "   → Không tìm thấy $SPORT_SEEKER_DIR, bỏ qua."
fi

echo "⏳ [5/6] Đang xóa SharedPreferences & cache..."
# Application Support (Flutter prefs)
for app_support_dir in "$HOME/Library/Application Support"/com.aibus*; do
    if [ -d "$app_support_dir" ]; then
        rm -rf "$app_support_dir"
        echo "   ✅ Đã xóa: $app_support_dir"
    fi
done

# NSUserDefaults plist
PLIST_DIR="$HOME/Library/Preferences"
for plist in "$PLIST_DIR"/com.aibus*.plist; do
    if [ -f "$plist" ]; then
        rm -f "$plist"
        echo "   ✅ Đã xóa prefs: $(basename "$plist")"
    fi
done

# Saved Application State
for saved_state in "$HOME/Library/Saved Application State"/com.aibus*; do
    if [ -d "$saved_state" ]; then
        rm -rf "$saved_state"
        echo "   ✅ Đã xóa saved state: $(basename "$saved_state")"
    fi
done

echo "⏳ [6/6] Đang xóa cache AI Models (.paddleocr, .insightface)..."
rm -rf "$HOME/.paddleocr" 2>/dev/null && echo "   ✅ Đã xóa ~/.paddleocr" || true
rm -rf "$HOME/.paddlex"   2>/dev/null && echo "   ✅ Đã xóa ~/.paddlex"   || true
rm -rf "$HOME/.insightface" 2>/dev/null && echo "   ✅ Đã xóa ~/.insightface" || true

echo ""
echo "✅ GỠ CÀI ĐẶT HOÀN TẤT!"
echo "   Sport Seeker đã được xóa hoàn toàn khỏi máy."
echo "==================================================="
echo ""

sleep 2
osascript -e 'tell application "Terminal" to close front window' 2>/dev/null || true
