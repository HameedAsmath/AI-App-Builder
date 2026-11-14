import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.lib.auth import get_current_user
from app.lib.db import get_session
from app.models import Project, User

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: str
    preview_url: str | None
    created_at: datetime


def to_out(p: Project) -> ProjectOut:
    return ProjectOut(id=p.id, name=p.name, preview_url=p.preview_url, created_at=p.created_at)


# Load a project only if it belongs to this user; otherwise 404
async def get_own_project(project_id: uuid.UUID, user: User, db: AsyncSession) -> Project:
    project = await db.scalar(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.get("")
async def list_projects(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)
) -> list[ProjectOut]:
    rows = await db.scalars(
        select(Project).where(Project.user_id == user.id).order_by(Project.created_at.desc())
    )
    return [to_out(p) for p in rows]


@router.post("", status_code=201)
async def create_project(
    body: ProjectCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)
) -> ProjectOut:
    project = Project(user_id=user.id, name=body.name)
    db.add(project)
    await db.commit()
    await db.refresh(project)  # reload to get created_at from the DB
    return to_out(project)


@router.get("/{project_id}")
async def get_project(
    project_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)
) -> ProjectOut:
    return to_out(await get_own_project(project_id, user, db))


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)
) -> None:
    project = await get_own_project(project_id, user, db)
    await db.delete(project)
    await db.commit()