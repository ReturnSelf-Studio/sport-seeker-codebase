#!/bin/bash
set -e

DIR=$(cd "$(dirname "$0")" && pwd)
ROOT_DIR="$DIR/.."
cd "$ROOT_DIR"

echo "=========================================="
echo "  🚀 SPORT SEEKER CLI TOOL (MACOS/LINUX)"
echo "=========================================="

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ [LỖI] Python3 chưa được cài đặt. Vui lòng cài Python 3.11+."
    exit 1
fi

# 2. Check/Install uv
if ! command -v uv &> /dev/null; then
    echo "⏳ [INFO] uv chưa được cài đặt. Đang tiến hành cài đặt uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# 3. Setup Virtual Environment (Minimal)
if [ ! -d ".venv" ]; then
    echo "⏳ [INFO] Đang tạo virtual environment..."
    uv venv --python 3.11
fi

# 4. Activate Virtual Environment
source .venv/bin/activate

# 5. Chuyển giao toàn bộ quyền điều khiển cho Python CLI
python3 scripts/cli.py "$@"
