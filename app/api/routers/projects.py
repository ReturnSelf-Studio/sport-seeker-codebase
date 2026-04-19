from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.project_manager import ProjectManager

router = APIRouter(prefix="/projects", tags=["Projects"])
pm = ProjectManager()

class ProjectCreate(BaseModel):
    name: str
    source_dir: str
    event_date: str = ""
    notes: str = ""

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    source_dir: Optional[str] = None
    event_date: Optional[str] = None
    notes: Optional[str] = None

@router.get("")
def get_projects():
    return {"projects": pm.list_projects()}

@router.post("")
def create_project(req: ProjectCreate):
    p = pm.create_project(req.name, req.source_dir, req.event_date, req.notes)
    return {"project": p}

@router.put("/{project_id}")
def update_project(project_id: str, req: ProjectUpdate):
    update_data = {k: v for k, v in req.dict().items() if v is not None}
    p = pm.update_project(project_id, **update_data)
    if not p:
        raise HTTPException(status_code=404, detail="Project không tồn tại")
    return {"project": p}

@router.delete("/{project_id}")
def delete_project(project_id: str, delete_files: bool = False):
    success = pm.delete_project(project_id, delete_files)
    if not success:
        raise HTTPException(status_code=404, detail="Project không tồn tại")
    return {"status": "ok"}
