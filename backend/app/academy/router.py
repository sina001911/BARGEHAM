"""Academy Foundation API endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Body, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.academy import service
from app.academy.models import (
    Course,
    CourseFolderLink,
    CourseProgress,
    LearnerMemory,
    CourseType,
)
from app.auth.router import get_current_user
from app.database import get_session
from app.users.models import User

router = APIRouter(prefix="/academy", tags=["academy"])


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #

class CourseCreate(BaseModel):
    name: str
    description: str | None = None
    course_type: CourseType = CourseType.PERSONAL
    is_active: bool = True


class CourseRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    course_type: CourseType
    owner_id: uuid.UUID
    is_active: bool
    embedding_model: str
    embedding_dim: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CourseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    course_type: CourseType | None = None
    is_active: bool | None = None


class FolderLinkCreate(BaseModel):
    course_id: uuid.UUID
    folder_id: uuid.UUID
    folder_path: str
    watch_enabled: bool = True


class FolderLinkRead(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    folder_id: uuid.UUID
    folder_path: str
    watch_enabled: bool
    created_at: datetime
    updated_at: datetime
    last_indexed: datetime | None = None

    class Config:
        from_attributes = True


class FolderLinkUpdate(BaseModel):
    watch_enabled: bool | None = None
    folder_path: str | None = None
    last_indexed: datetime | None = None


class LearnerMemoryCreate(BaseModel):
    course_id: uuid.UUID
    user_id: uuid.UUID
    topic: str
    mastery_level: float | None = None
    confidence: float | None = None
    test_results: str | None = None
    mistakes: str | None = None
    weaknesses: str | None = None
    goals: str | None = None
    preferences: str | None = None
    review_schedule: str | None = None
    progress_summary: str | None = None


class LearnerMemoryRead(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    user_id: uuid.UUID
    topic: str
    mastery_level: float
    confidence: float
    test_results: str | None = None
    mistakes: str | None = None
    weaknesses: str | None = None
    goals: str | None = None
    preferences: str | None = None
    review_schedule: str | None = None
    progress_summary: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LearnerMemoryUpdate(BaseModel):
    mastery_level: float | None = None
    confidence: float | None = None
    test_results: str | None = None
    mistakes: str | None = None
    weaknesses: str | None = None
    goals: str | None = None
    preferences: str | None = None
    review_schedule: str | None = None
    progress_summary: str | None = None


class CourseProgressRead(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    user_id: uuid.UUID
    documents_indexed: int
    chunks_indexed: int
    lessons_completed: int
    quizzes_taken: int
    average_score: float
    last_activity: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --------------------------------------------------------------------------- #
# Course endpoints
# --------------------------------------------------------------------------- #

@router.post("/courses", response_model=CourseRead, status_code=201)
async def create_course_endpoint(
    req: CourseCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new Academy course."""
    course = await service.create_course(
        session,
        name=req.name,
        description=req.description,
        course_type=req.course_type,
        owner_id=current_user.id,
        is_active=req.is_active,
    )
    return course


@router.get("/courses", response_model=list[CourseRead])
async def list_courses_endpoint(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    course_type: CourseType | None = Query(default=None),
    is_active: bool | None = Query(default=True),
):
    """List courses for the current user."""
    return await service.list_courses(
        session,
        owner_id=current_user.id,
        is_active=is_active,
        course_type=course_type,
    )


@router.get("/courses/{course_id}", response_model=CourseRead)
async def get_course_endpoint(
    course_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a course by ID."""
    course = await service.get_course(session, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")
    return course


@router.patch("/courses/{course_id}", response_model=CourseRead)
async def update_course_endpoint(
    course_id: uuid.UUID,
    req: CourseUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update a course."""
    course = await service.get_course(session, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")
    updated = await service.update_course(
        session,
        course_id,
        name=req.name,
        description=req.description,
        course_type=req.course_type,
        is_active=req.is_active,
    )
    return updated


@router.delete("/courses/{course_id}", status_code=204)
async def delete_course_endpoint(
    course_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a course."""
    course = await service.get_course(session, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")
    ok = await service.delete_course(session, course_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Course not found")


# --------------------------------------------------------------------------- #
# Course-Folder Link endpoints
# --------------------------------------------------------------------------- #

@router.post("/folder-links", response_model=FolderLinkRead, status_code=201)
async def link_folder_to_course_endpoint(
    req: FolderLinkCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Link a real system folder to a course for incremental indexing."""
    # Verify course ownership
    course = await service.get_course(session, req.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")

    link = await service.link_folder_to_course(
        session,
        course_id=req.course_id,
        folder_id=req.folder_id,
        folder_path=req.folder_path,
        watch_enabled=req.watch_enabled,
    )
    return link


@router.get("/folder-links", response_model=list[FolderLinkRead])
async def list_folder_links_endpoint(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    course_id: uuid.UUID | None = Query(default=None),
    folder_id: uuid.UUID | None = Query(default=None),
    watch_enabled: bool | None = Query(default=None),
):
    """List course-folder links."""
    return await service.list_folder_links(
        session,
        course_id=course_id,
        folder_id=folder_id,
        watch_enabled=watch_enabled,
    )


@router.patch("/folder-links/{link_id}", response_model=FolderLinkRead)
async def update_folder_link_endpoint(
    link_id: uuid.UUID,
    req: FolderLinkUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update a course-folder link."""
    link = await session.get(CourseFolderLink, link_id)
    if link is None:
        raise HTTPException(status_code=404, detail="Folder link not found")
    course = await service.get_course(session, link.course_id)
    if course is None or course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")

    updated = await service.update_folder_link(
        session,
        link_id,
        watch_enabled=req.watch_enabled,
        folder_path=req.folder_path,
        last_indexed=req.last_indexed,
    )
    return updated


@router.delete("/folder-links/{link_id}", status_code=204)
async def delete_folder_link_endpoint(
    link_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a course-folder link."""
    link = await session.get(CourseFolderLink, link_id)
    if link is None:
        raise HTTPException(status_code=404, detail="Folder link not found")
    course = await service.get_course(session, link.course_id)
    if course is None or course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")
    ok = await service.delete_folder_link(session, link_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Folder link not found")


# --------------------------------------------------------------------------- #
# Learner Memory endpoints
# --------------------------------------------------------------------------- #

@router.post("/learner-memory", response_model=LearnerMemoryRead, status_code=201)
async def upsert_learner_memory_endpoint(
    req: LearnerMemoryCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create or update learner memory for a topic within a course."""
    course = await service.get_course(session, req.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")

    memory = await service.upsert_learner_memory(
        session,
        course_id=req.course_id,
        user_id=req.user_id,
        topic=req.topic,
        mastery_level=req.mastery_level,
        confidence=req.confidence,
        test_results=req.test_results,
        mistakes=req.mistakes,
        weaknesses=req.weaknesses,
        goals=req.goals,
        preferences=req.preferences,
        review_schedule=req.review_schedule,
        progress_summary=req.progress_summary,
    )
    return memory


@router.get("/learner-memory", response_model=list[LearnerMemoryRead])
async def list_learner_memories_endpoint(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    course_id: uuid.UUID | None = Query(default=None),
    topic: str | None = Query(default=None),
):
    """List learner memories."""
    return await service.list_learner_memories(
        session,
        course_id=course_id,
        user_id=current_user.id,
        topic=topic,
    )


@router.get("/learner-memory/{course_id}/{topic}", response_model=LearnerMemoryRead)
async def get_learner_memory_endpoint(
    course_id: uuid.UUID,
    topic: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get learner memory for a specific course and topic."""
    memory = await service.get_learner_memory(session, course_id, current_user.id, topic)
    if memory is None:
        raise HTTPException(status_code=404, detail="Learner memory not found")
    return memory


@router.delete("/learner-memory/{course_id}/{topic}", status_code=204)
async def delete_learner_memory_endpoint(
    course_id: uuid.UUID,
    topic: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete learner memory for a specific course and topic."""
    ok = await service.delete_learner_memory(session, course_id, current_user.id, topic)
    if not ok:
        raise HTTPException(status_code=404, detail="Learner memory not found")


# --------------------------------------------------------------------------- #
# Course Progress endpoints
# --------------------------------------------------------------------------- #

@router.get("/progress/{course_id}", response_model=CourseProgressRead)
async def get_course_progress_endpoint(
    course_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get course progress for the current user."""
    progress = await service.get_course_progress(session, course_id, current_user.id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Course progress not found")
    return progress


@router.post("/progress/{course_id}", response_model=CourseProgressRead)
async def upsert_course_progress_endpoint(
    course_id: uuid.UUID,
    documents_indexed: int | None = Body(default=None),
    chunks_indexed: int | None = Body(default=None),
    lessons_completed: int | None = Body(default=None),
    quizzes_taken: int | None = Body(default=None),
    average_score: float | None = Body(default=None),
    last_activity: datetime | None = Body(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create or update course progress for the current user."""
    course = await service.get_course(session, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")

    progress = await service.upsert_course_progress(
        session,
        course_id=course_id,
        user_id=current_user.id,
        documents_indexed=documents_indexed,
        chunks_indexed=chunks_indexed,
        lessons_completed=lessons_completed,
        quizzes_taken=quizzes_taken,
        average_score=average_score,
        last_activity=last_activity,
    )
    return progress
