#!/bin/bash
# .claude/sync.sh
# Copy các file đã patch từ codebase-minimal sang codebase-main
# Chạy từ bất kỳ đâu: bash /Users/arlix/projects/AIBus-SportSeeker/codebase-minimal/.claude/sync.sh

MINIMAL="/Users/arlix/projects/AIBus-SportSeeker/codebase-minimal"
MAIN="/Users/arlix/projects/AIBus-SportSeeker/codebase-main"

echo "🔄 Syncing minimal → main..."

copy_file() {
  local rel_path="$1"
  local src="$MINIMAL/$rel_path"
  local dst="$MAIN/$rel_path"

  if [ ! -f "$src" ]; then
    echo "  ⚠ Không tìm thấy: $rel_path"
    return
  fi

  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  echo "  ✅ $rel_path"
}

# Backend
copy_file "resource/backend/app/core/video_manifest.py"
copy_file "resource/backend/app/core/project_manager.py"
copy_file "resource/backend/app/api/routers/engine.py"
copy_file "resource/backend/app/services/video_pipeline.py"

# Frontend
copy_file "lib/ui/pages/workspace_page.dart"
copy_file "lib/ui/pages/workspace/workspace_actions.dart"
copy_file "lib/ui/pages/workspace/workspace_prescan_widget.dart"
copy_file "lib/ui/pages/workspace/workspace_control_widget.dart"

echo ""
echo "✅ Sync xong. Giờ có thể build từ: $MAIN"
