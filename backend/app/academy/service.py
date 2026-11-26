"""Academy Foundation service: courses, folder links, learner memory, progress."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import or_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.documents.models import Document, Folder
from app.academy.models import (
    Course,
    CourseFolderLink,
    CourseProgress,
    LearnerMemory,
    CourseType,
)

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Course CRUD
# --------------------------------------------------------------------------- #

async def create_course(
    session: AsyncSession,
    *,
    name: str,
    description: str | None = None,
    course_type: CourseType = CourseType.PERSONAL,
    owner_id: uuid.UUID,
    is_active: bool = True,
) -> Course:
    course = Course(
        name=name,
        description=description,
        course_type=course_type,
        owner_id=owner_id,
        is_active=is_active,
    )
    session.add(course)
    await session.commit()
    await session.refresh(course)
    return course


async def list_courses(
    session: AsyncSession,
    *,
    owner_id: uuid.UUID | None = None,
    is_active: bool | None = True,
    course_type: CourseType | None = None,
) -> list[Course]:
    stmt = select(Course)
    conditions = []
    if owner_id is not None:
        conditions.append(Course.owner_id == owner_id)
    if is_active is not None:
        conditions.append(Course.is_active == is_active)
    if course_type is not None:
        conditions.append(Course.course_type == course_type)
    if conditions:
        stmt = stmt.where(or_(*conditions))
    stmt = stmt.order_by(Course.name)
    return list((await session.execute(stmt)).scalars().all())


async def get_course(session: AsyncSession, course_id: uuid.UUID) -> Course | None:
    return await session.get(Course, course_id)


async def update_course(
    session: AsyncSession,
    course_id: uuid.UUID,
    *,
    name: str | None = None,
    description: str | None = None,
    course_type: CourseType | None = None,
    is_active: bool | None = None,
) -> Course | None:
    course = await get_course(session, course_id)
    if course is None:
        return None
    if name is not None:
        course.name = name
    if description is not None:
        course.description = description
    if course_type is not None:
        course.course_type = course_type
    if is_active is not None:
        course.is_active = is_active
    course.updated_at = _utcnow()
    session.add(course)
    await session.commit()
    await session.refresh(course)
    return course


async def delete_course(session: AsyncSession, course_id: uuid.UUID) -> bool:
    course = await get_course(session, course_id)
    if course is None:
        return False
    await session.delete(course)
    await session.commit()
    return True


# --------------------------------------------------------------------------- #
# Course-Folder Link (Folder Watcher integration)
# --------------------------------------------------------------------------- #

async def link_folder_to_course(
    session: AsyncSession,
    *,
    course_id: uuid.UUID,
    folder_id: uuid.UUID,
    folder_path: str,
    watch_enabled: bool = True,
) -> CourseFolderLink:
    link = CourseFolderLink(
        course_id=course_id,
        folder_id=folder_id,
        folder_path=folder_path,
        watch_enabled=watch_enabled,
    )
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


async def list_folder_links(
    session: AsyncSession,
    *,
    course_id: uuid.UUID | None = None,
    folder_id: uuid.UUID | None = None,
    watch_enabled: bool | None = None,
) -> list[CourseFolderLink]:
    stmt = select(CourseFolderLink)
    conditions = []
    if course_id is not None:
        conditions.append(CourseFolderLink.course_id == course_id)
    if folder_id is not None:
        conditions.append(CourseFolderLink.folder_id == folder_id)
    if watch_enabled is not None:
        conditions.append(CourseFolderLink.watch_enabled == watch_enabled)
    if conditions:
        stmt = stmt.where(or_(*conditions))
    stmt = stmt.order_by(CourseFolderLink.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())


async def update_folder_link(
    session: AsyncSession,
    link_id: uuid.UUID,
    *,
    watch_enabled: bool | None = None,
    folder_path: str | None = None,
    last_indexed: datetime | None = None,
) -> CourseFolderLink | None:
    link = await session.get(CourseFolderLink, link_id)
    if link is None:
        return None
    if watch_enabled is not None:
        link.watch_enabled = watch_enabled
    if folder_path is not None:
        link.folder_path = folder_path
    if last_indexed is not None:
        link.last_indexed = last_indexed
    link.updated_at = _utcnow()
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


async def delete_folder_link(session: AsyncSession, link_id: uuid.UUID) -> bool:
    link = await session.get(CourseFolderLink, link_id)
    if link is None:
        return False
    await session.delete(link)
    await session.commit()
    return True


# --------------------------------------------------------------------------- #
# Learner Memory (persistent, course-isolated)
# --------------------------------------------------------------------------- #

async def upsert_learner_memory(
    session: AsyncSession,
    *,
    course_id: uuid.UUID,
    user_id: uuid.UUID,
    topic: str,
    mastery_level: float | None = None,
    confidence: float | None = None,
    test_results: str | None = None,
    mistakes: str | None = None,
    weaknesses: str | None = None,
    goals: str | None = None,
    preferences: str | None = None,
    review_schedule: str | None = None,
    progress_summary: str | None = None,
) -> LearnerMemory:
    """Create or update learner memory for a topic within a course."""
    stmt = select(LearnerMemory).where(
        LearnerMemory.course_id == course_id,
        LearnerMemory.user_id == user_id,
        LearnerMemory.topic == topic,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()

    if existing:
        if mastery_level is not None:
            existing.mastery_level = mastery_level
        if confidence is not None:
            existing.confidence = confidence
        if test_results is not None:
            existing.test_results = test_results
        if mistakes is not None:
            existing.mistakes = mistakes
        if weaknesses is not None:
            existing.weaknesses = weaknesses
        if goals is not None:
            existing.goals = goals
        if preferences is not None:
            existing.preferences = preferences
        if review_schedule is not None:
            existing.review_schedule = review_schedule
        if progress_summary is not None:
            existing.progress_summary = progress_summary
        existing.updated_at = _utcnow()
        session.add(existing)
        await session.commit()
        await session.refresh(existing)
        return existing
    else:
        memory = LearnerMemory(
            course_id=course_id,
            user_id=user_id,
            topic=topic,
            mastery_level=mastery_level or 0.0,
            confidence=confidence or 0.0,
            test_results=test_results,
            mistakes=mistakes,
            weaknesses=weaknesses,
            goals=goals,
            preferences=preferences,
            review_schedule=review_schedule,
            progress_summary=progress_summary,
        )
        session.add(memory)
        await session.commit()
        await session.refresh(memory)
        return memory


async def list_learner_memories(
    session: AsyncSession,
    *,
    course_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    topic: str | None = None,
) -> list[LearnerMemory]:
    stmt = select(LearnerMemory)
    conditions = []
    if course_id is not None:
        conditions.append(LearnerMemory.course_id == course_id)
    if user_id is not None:
        conditions.append(LearnerMemory.user_id == user_id)
    if topic is not None:
        conditions.append(LearnerMemory.topic == topic)
    if conditions:
        stmt = stmt.where(or_(*conditions))
    stmt = stmt.order_by(LearnerMemory.topic)
    return list((await session.execute(stmt)).scalars().all())


async def get_learner_memory(
    session: AsyncSession, course_id: uuid.UUID, user_id: uuid.UUID, topic: str
) -> LearnerMemory | None:
    stmt = select(LearnerMemory).where(
        LearnerMemory.course_id == course_id,
        LearnerMemory.user_id == user_id,
        LearnerMemory.topic == topic,
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def delete_learner_memory(
    session: AsyncSession, course_id: uuid.UUID, user_id: uuid.UUID, topic: str
) -> bool:
    memory = await get_learner_memory(session, course_id, user_id, topic)
    if memory is None:
        return False
    await session.delete(memory)
    await session.commit()
    return True


# --------------------------------------------------------------------------- #
# Course Progress
# --------------------------------------------------------------------------- #

async def upsert_course_progress(
    session: AsyncSession,
    *,
    course_id: uuid.UUID,
    user_id: uuid.UUID,
    documents_indexed: int | None = None,
    chunks_indexed: int | None = None,
    lessons_completed: int | None = None,
    quizzes_taken: int | None = None,
    average_score: float | None = None,
    last_activity: datetime | None = None,
) -> CourseProgress:
    stmt = select(CourseProgress).where(
        CourseProgress.course_id == course_id,
        CourseProgress.user_id == user_id,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()

    if existing:
        if documents_indexed is not None:
            existing.documents_indexed = documents_indexed
        if chunks_indexed is not None:
            existing.chunks_indexed = chunks_indexed
        if lessons_completed is not None:
            existing.lessons_completed = lessons_completed
        if quizzes_taken is not None:
            existing.quizzes_taken = quizzes_taken
        if average_score is not None:
            existing.average_score = average_score
        if last_activity is not None:
            existing.last_activity = last_activity
        existing.updated_at = _utcnow()
        session.add(existing)
        await session.commit()
        await session.refresh(existing)
        return existing
    else:
        progress = CourseProgress(
            course_id=course_id,
            user_id=user_id,
            documents_indexed=documents_indexed or 0,
            chunks_indexed=chunks_indexed or 0,
            lessons_completed=lessons_completed or 0,
            quizzes_taken=quizzes_taken or 0,
            average_score=average_score or 0.0,
            last_activity=last_activity,
        )
        session.add(progress)
        await session.commit()
        await session.refresh(progress)
        return progress


async def get_course_progress(
    session: AsyncSession, course_id: uuid.UUID, user_id: uuid.UUID
) -> CourseProgress | None:
    stmt = select(CourseProgress).where(
        CourseProgress.course_id == course_id,
        CourseProgress.user_id == user_id,
    )
    return (await session.execute(stmt)).scalar_one_or_none()


# --------------------------------------------------------------------------- #
# Course Isolation - verify user owns course
# --------------------------------------------------------------------------- #

async def verify_course_owner(
    session: AsyncSession, course_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    """Return True if the user owns the course (course isolation check)."""
    stmt = select(Course).where(
        Course.id == course_id,
        Course.owner_id == user_id,
    )
    return (await session.execute(stmt)).scalar_one_or_none() is not None
