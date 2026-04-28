"""
app/core/video_manifest.py

VideoManifest: quản lý trạng thái quét từng video trong project.
Lưu tại project_dir/.ss_meta/video_manifest.json
Key = tên file (không phải full path) — đổi tên = video mới.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
META_DIR = ".ss_meta"
MANIFEST_FILE = "video_manifest.json"


class VideoManifest:
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.meta_dir = self.project_dir / META_DIR
        self.manifest_path = self.meta_dir / MANIFEST_FILE
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self._data: dict = self._load()

    # ── I/O ──────────────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def save(self):
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    # ── Scan source_dir ───────────────────────────────────────────────────────

    def sync_with_source(self, source_dir: str) -> dict:
        """
        Scan source_dir, đồng bộ manifest:
        - Video mới (chưa có trong manifest) → thêm với status "no-scan", đọc total_frames
        - Video đã có nhưng thiếu total_frames → backfill
        - Video đã xóa khỏi folder → giữ nguyên trong manifest (không tự xóa)
        Returns summary dict.
        """
        src = Path(source_dir)
        found_names = set()

        for f in src.rglob("*"):
            if f.suffix.lower() in VIDEO_EXTENSIONS and META_DIR not in f.parts:
                name = f.name
                found_names.add(name)
                entry = self._data.get(name)

                if entry is None:
                    # Video mới — đọc metadata đầy đủ
                    size, total_frames, fps = 0, None, None
                    try:
                        size = f.stat().st_size
                    except OSError:
                        pass
                    try:
                        import cv2 as _cv2
                        cap = _cv2.VideoCapture(str(f))
                        if cap.isOpened():
                            total_frames = int(cap.get(_cv2.CAP_PROP_FRAME_COUNT))
                            fps = cap.get(_cv2.CAP_PROP_FPS) or None
                            cap.release()
                    except Exception:
                        pass

                    self._data[name] = {
                        "size_bytes": size,
                        "total_frames": total_frames,
                        "fps": fps,
                        "duration_seconds": (total_frames / fps) if (total_frames and fps) else None,
                        "scan_status": "no-scan",
                        "last_scanned_at": None,
                        "scan_version": 0,
                    }
                elif entry.get("total_frames") is None:
                    # Video cũ chưa có total_frames — backfill
                    try:
                        import cv2 as _cv2
                        cap = _cv2.VideoCapture(str(f))
                        if cap.isOpened():
                            tf = int(cap.get(_cv2.CAP_PROP_FRAME_COUNT))
                            fp = cap.get(_cv2.CAP_PROP_FPS) or None
                            cap.release()
                            entry["total_frames"] = tf
                            entry["fps"] = fp
                            if not entry.get("duration_seconds") and fp:
                                entry["duration_seconds"] = tf / fp
                    except Exception:
                        pass

        self.save()

        total = len(found_names)
        done = sum(1 for n in found_names if self._data.get(n, {}).get("scan_status") == "done")
        pending = total - done

        return {
            "total": total,
            "done": done,
            "pending": pending,
            "video_names": sorted(found_names),
        }

    # ── Status helpers ────────────────────────────────────────────────────────

    def get_pending_videos(self, source_dir: str) -> list[str]:
        """Trả về full path các video chưa quét (hoặc quét lại được yêu cầu)."""
        src = Path(source_dir)
        result = []
        for f in sorted(src.rglob("*")):
            if f.suffix.lower() in VIDEO_EXTENSIONS and META_DIR not in f.parts:
                entry = self._data.get(f.name, {})
                if entry.get("scan_status") != "done":
                    result.append(str(f))
        return result

    def get_all_videos(self, source_dir: str) -> list[dict]:
        """Trả về list dict cho từng video trong source_dir kèm status."""
        src = Path(source_dir)
        result = []
        for f in sorted(src.rglob("*")):
            if f.suffix.lower() in VIDEO_EXTENSIONS and META_DIR not in f.parts:
                entry = self._data.get(f.name, {
                    "size_bytes": 0,
                    "duration_seconds": None,
                    "scan_status": "no-scan",
                    "last_scanned_at": None,
                    "scan_version": 0,
                })
                result.append({
                    "name": f.name,
                    "path": str(f),
                    **entry,
                })
        return result

    def mark_scanning(self, video_name: str):
        """Đánh dấu video đang được quét (trạng thái tạm thời)."""
        if video_name in self._data:
            self._data[video_name]["scan_status"] = "scanning"
            self.save()

    def mark_done(self, video_name: str, duration_seconds: Optional[float] = None):
        """Đánh dấu video đã quét xong, update metadata."""
        if video_name not in self._data:
            self._data[video_name] = {}
        entry = self._data[video_name]
        entry["scan_status"] = "done"
        entry["last_scanned_at"] = datetime.now().isoformat()
        entry["scan_version"] = entry.get("scan_version", 0) + 1
        if duration_seconds is not None:
            entry["duration_seconds"] = duration_seconds
        self.save()

    def mark_failed(self, video_name: str):
        """Reset video về no-scan nếu quét dở (bị interrupt)."""
        if video_name in self._data:
            self._data[video_name]["scan_status"] = "no-scan"
            self.save()

    def reset_all_scanning(self):
        """Khi app restart, reset mọi entry "scanning" về "no-scan" (crash recovery)."""
        changed = False
        for entry in self._data.values():
            if entry.get("scan_status") == "scanning":
                entry["scan_status"] = "no-scan"
                changed = True
        if changed:
            self.save()

    def get_status(self, video_name: str) -> str:
        return self._data.get(video_name, {}).get("scan_status", "no-scan")


# ── Index backup/restore ──────────────────────────────────────────────────────

def backup_index(project_dir: str) -> Optional[str]:
    """
    Backup toàn bộ index folder trước khi start session.
    Returns backup path hoặc None nếu không có gì để backup.
    """
    index_dir = Path(project_dir) / "index"
    backup_dir = Path(project_dir) / META_DIR / "index_backup"

    if not index_dir.exists():
        return None

    # Kiểm tra có file nào không
    files = list(index_dir.rglob("*"))
    if not any(f.is_file() for f in files):
        return None

    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    shutil.copytree(index_dir, backup_dir)
    return str(backup_dir)


def restore_index(project_dir: str) -> bool:
    """
    Restore index từ backup. Returns True nếu thành công.
    """
    index_dir = Path(project_dir) / "index"
    backup_dir = Path(project_dir) / META_DIR / "index_backup"

    if not backup_dir.exists():
        # Không có backup = index rỗng ban đầu, xóa index hiện tại
        if index_dir.exists():
            shutil.rmtree(index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        return True

    try:
        if index_dir.exists():
            shutil.rmtree(index_dir)
        shutil.copytree(backup_dir, index_dir)
        return True
    except Exception as e:
        print(f"[VideoManifest] Lỗi restore index: {e}")
        return False


def clear_backup(project_dir: str):
    """Xóa backup sau khi session hoàn tất thành công."""
    backup_dir = Path(project_dir) / META_DIR / "index_backup"
    if backup_dir.exists():
        shutil.rmtree(backup_dir, ignore_errors=True)
