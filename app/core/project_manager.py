"""
app/core/project_manager.py

ProjectManager: create/open/list/update/delete projects.
Mỗi project = named folder với FAISS index riêng.
Persist registry vào ~/SportSeeker/projects/projects.json.
"""

import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from app.core.config import settings

WORKSPACE_ROOT = Path.home() / "SportSeeker" / "projects"

class ProjectManager:
    def __init__(self, workspace_root: str | None = None):
        self.workspace_root = Path(workspace_root) if workspace_root else WORKSPACE_ROOT
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self._registry_path = self.workspace_root / "projects.json"

    def _load_registry(self) -> list[dict]:
        if self._registry_path.exists():
            try:
                with open(self._registry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def _save_registry(self, projects: list[dict]):
        with open(self._registry_path, "w", encoding="utf-8") as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)

    def create_project(self, name: str, source_dir: str,
                       event_date: str = "", notes: str = "") -> dict:
        """
        Tạo project mới: folder riêng + entry trong registry.
        Returns project dict. Raise ValueError nếu trùng tên.
        """
        projects = self._load_registry()
        
        # --- BẮT ĐẦU THÊM CHECK TRÙNG TÊN ---
        target_name_lower = name.strip().lower()
        if any(p.get("name", "").strip().lower() == target_name_lower for p in projects):
            raise ValueError("Tên dự án đã tồn tại")
        # --- KẾT THÚC THÊM CHECK TRÙNG TÊN ---

        project_id = str(uuid.uuid4())[:8]
        safe_name = _safe_dirname(name)
        project_dir = str(self.workspace_root / f"{safe_name}_{project_id}")
        os.makedirs(os.path.join(project_dir, "index"), exist_ok=True)

        project = {
            "id": project_id,
            "name": name,
            "source_dir": source_dir,
            "project_dir": project_dir,
            "event_date": event_date,
            "notes": notes,
            "created_at": datetime.now().isoformat(),
        }

        projects.append(project)
        self._save_registry(projects)
        return project

    def list_projects(self) -> list[dict]:
        """
        Trả về tất cả projects, enriched với live stats.
        """
        projects = self._load_registry()
        for p in projects:
            _enrich(p)
        return projects

    def get_project(self, project_id: str) -> dict | None:
        for p in self._load_registry():
            if p.get("id") == project_id:
                _enrich(p)
                return p
        return None

    def update_project(self, project_id: str, **kwargs) -> dict | None:
        """
        Update fields của project (name, source_dir, event_date, notes).
        project_dir và id không thay đổi.
        """
        projects = self._load_registry()
        for p in projects:
            if p.get("id") == project_id:
                safe_fields = {"name", "source_dir", "event_date", "notes"}
                for k, v in kwargs.items():
                    if k in safe_fields:
                        p[k] = v
                p["updated_at"] = datetime.now().isoformat()
                self._save_registry(projects)
                _enrich(p)
                return p
        return None

    def delete_project(self, project_id: str, delete_files: bool = False) -> bool:
        """
        Xóa project khỏi registry.
        delete_files=True: xóa cả folder project (index + data).
        Source dir KHÔNG bị xóa.
        """
        projects = self._load_registry()
        target = next((p for p in projects if p.get("id") == project_id), None)
        if not target:
            return False

        if delete_files:
            project_dir = target.get("project_dir", "")
            if project_dir and os.path.exists(project_dir):
                shutil.rmtree(project_dir, ignore_errors=True)

        new_list = [p for p in projects if p.get("id") != project_id]
        self._save_registry(new_list)
        return True

    def get_index_paths(self, project_id: str) -> dict | None:
        """
        Trả về dict các path index của project.
        Dùng để patch settings trước khi khởi tạo VectorStore.
        """
        p = self.get_project(project_id)
        if not p:
            return None
        index_dir = os.path.join(p["project_dir"], "index")
        return {
            "INDEX_PATH": os.path.join(index_dir, "index.faiss"),
            "METADATA_PATH": os.path.join(index_dir, "metadata.parquet"),
            "BIB_INDEX_PATH": os.path.join(index_dir, "bib_index.faiss"),
            "BIB_METADATA_PATH": os.path.join(index_dir, "bib_metadata.parquet"),
        }

    def apply_index_paths(self, project_id: str) -> bool:
        """
        Patch settings với index paths của project.
        Gọi trước khi khởi tạo VectorStore.
        """
        paths = self.get_index_paths(project_id)
        if not paths:
            return False
        for attr, val in paths.items():
            setattr(settings, attr, val)
        return True

def _safe_dirname(name: str) -> str:
    """Convert tên project thành tên folder an toàn."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:40]

def _enrich(p: dict):
    """Thêm live stats vào project dict."""
    project_dir = p.get("project_dir", "")
    index_path = os.path.join(project_dir, "index", "index.faiss")
    p["has_index"] = os.path.exists(index_path)

    source_dir = p.get("source_dir", "")
    if os.path.exists(source_dir):
        exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp",
                ".mp4", ".avi", ".mov", ".mkv"}
        try:
            count = sum(
                1 for f in Path(source_dir).rglob("*")
                if f.suffix.lower() in exts
            )
        except PermissionError:
            count = 0
        p["media_count"] = count
    else:
        p["media_count"] = p.get("media_count", 0)
