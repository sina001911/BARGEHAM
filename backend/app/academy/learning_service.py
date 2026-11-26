"""Academy Intelligence Learning Tools service: flashcards, spaced repetition, practice, language learning, study planner, analytics."""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.academy.intelligence_models import LessonUserProgress
from app.academy.learning_models import (
    Flashcard,
    FlashcardReview,
    LanguageExercise,
    LanguageExerciseAttempt,
    LearningAnalytics,
    LearningGoal,
    PracticeAttempt,
    PracticeProblem,
    StudySession,
)
from app.academy.models import Course, LearnerMemory

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Flashcard Service
# --------------------------------------------------------------------------- #

async def create_flashcard(
    session: AsyncSession,
    *,
    course_id: uuid.UUID,
    user_id: uuid.UUID,
    front: str,
    back: str,
    card_type: str = "text",
) -> Flashcard:
    """Create a new flashcard."""
    card = Flashcard(
        course_id=course_id,
        user_id=user_id,
        front=front,
        back=back,
        card_type=card_type,
    )
    session.add(card)
    await session.commit()
    await session.refresh(card)
    return card


async def list_flashcards(
    session: AsyncSession,
    *,
    course_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    card_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[Flashcard]:
    """List flashcards with optional filtering."""
    stmt = __import__("sqlalchemy").select(Flashcard)
    conditions = []
    if course_id is not None:
        conditions.append(Flashcard.course_id == course_id)
    if user_id is not None:
        conditions.append(Flashcard.user_id == user_id)
    if card_type is not None:
        conditions.append(Flashcard.card_type == card_type)
    if status is not None:
        conditions.append(Flashcard.status == status)
    if conditions:
        stmt = stmt.where(__import__("sqlalchemy").or_(*conditions))
    stmt = stmt.order_by(Flashcard.next_review.asc(), Flashcard.created_at.desc()).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def get_flashcard(session: AsyncSession, card_id: uuid.UUID) -> Flashcard | None:
    """Get a flashcard by ID."""
    return await session.get(Flashcard, card_id)


async def update_flashcard(
    session: AsyncSession,
    card_id: uuid.UUID,
    *,
    front: str | None = None,
    back: str | None = None,
    card_type: str | None = None,
    status: str | None = None,
    interval_days: int | None = None,
    repetitions: int | None = None,
    next_review: datetime | None = None,
) -> Flashcard | None:
    """Update a flashcard."""
    card = await session.get(Flashcard, card_id)
    if card is None:
        return None
    if front is not None:
        card.front = front
    if back is not None:
        card.back = back
    if card_type is not None:
        card.card_type = card_type  # type: ignore[assignment]
    if status is not None:
        card.status = status  # type: ignore[assignment]
    if interval_days is not None:
        card.interval_days = interval_days
    if repetitions is not None:
        card.repetitions = repetitions
    if next_review is not None:
        card.next_review = next_review
    card.updated_at = _utcnow()
    session.add(card)
    await session.commit()
    await session.refresh(card)
    return card


async def delete_flashcard(session: AsyncSession, card_id: uuid.UUID) -> bool:
    """Delete a flashcard."""
    card = await session.get(Flashcard, card_id)
    if card is None:
        return False
    await session.delete(card)
    await session.commit()
    return True


# --------------------------------------------------------------------------- #
# Study Session Service
# --------------------------------------------------------------------------- #

async def create_study_session(
    session: AsyncSession,
    *,
    course_id: uuid.UUID | None,
    user_id: uuid.UUID,
    session_type: str = "study",
) -> StudySession:
    """Create a new study session."""
    session_obj = StudySession(
        course_id=course_id,
        user_id=user_id,
        session_type=session_type,
    )
    session.add(session_obj)
    await session.commit()
    await session.refresh(session_obj)
    return session_obj


async def end_study_session(
    session: AsyncSession,
    session_id: uuid.UUID,
    *,
    duration_minutes: int | None = None,
    items_studied: int | None = None,
    items_correct: int | None = None,
    notes: str | None = None,
) -> StudySession | None:
    """End a study session."""
    study_session = await session.get(StudySession, session_id)
    if study_session is None:
        return None
    study_session.ended_at = _utcnow()
    if duration_minutes is not None:
        study_session.duration_minutes = duration_minutes
    if items_studied is not None:
        study_session.items_studied = items_studied
    if items_correct is not None:
        study_session.items_correct = items_correct
    if notes is not None:
        study_session.notes = notes
    study_session.updated_at = _utcnow()
    session.add(study_session)
    await session.commit()
    await session.refresh(study_session)
    return study_session


async def list_study_sessions(
    session: AsyncSession,
    *,
    user_id: uuid.UUID | None = None,
    course_id: uuid.UUID | None = None,
    session_type: str | None = None,
    limit: int = 50,
) -> list[StudySession]:
    """List study sessions."""
    stmt = __import__("sqlalchemy").select(StudySession)
    conditions = []
    if user_id is not None:
        conditions.append(StudySession.user_id == user_id)
    if course_id is not None:
        conditions.append(StudySession.course_id == course_id)
    if session_type is not None:
        conditions.append(StudySession.session_type == session_type)
    if conditions:
        stmt = stmt.where(__import__("sqlalchemy").or_(*conditions))
    stmt = stmt.order_by(StudySession.started_at.desc()).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


# --------------------------------------------------------------------------- #
# Learning Goal Service
# --------------------------------------------------------------------------- #

async def create_learning_goal(
    session: AsyncSession,
    *,
    course_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str,
    description: str | None = None,
    target_date: datetime | None = None,
) -> LearningGoal:
    """Create a new learning goal."""
    goal = LearningGoal(
        course_id=course_id,
        user_id=user_id,
        title=title,
        description=description,
        target_date=target_date,
    )
    session.add(goal)
    await session.commit()
    await session.refresh(goal)
    return goal


async def list_learning_goals(
    session: AsyncSession,
    *,
    user_id: uuid.UUID | None = None,
    course_id: uuid.UUID | None = None,
    is_completed: bool | None = None,
) -> list[LearningGoal]:
    """List learning goals."""
    stmt = __import__("sqlalchemy").select(LearningGoal)
    conditions = []
    if user_id is not None:
        conditions.append(LearningGoal.user_id == user_id)
    if course_id is not None:
        conditions.append(LearningGoal.course_id == course_id)
    if is_completed is not None:
        conditions.append(LearningGoal.is_completed == is_completed)
    if conditions:
        stmt = stmt.where(__import__("sqlalchemy").or_(*conditions))
    stmt = stmt.order_by(LearningGoal.target_date.asc(), LearningGoal.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())


async def get_learning_goal(
    session: AsyncSession, goal_id: uuid.UUID
) -> LearningGoal | None:
    """Get a learning goal by ID."""
    goal = await session.get(LearningGoal, goal_id)
    if goal is None:
        return None
    return goal


async def update_learning_goal(
    session: AsyncSession,
    goal_id: uuid.UUID,
    *,
    title: str | None = None,
    description: str | None = None,
    target_date: datetime | None = None,
    is_completed: bool | None = None,
) -> LearningGoal | None:
    """Update a learning goal."""
    goal = await session.get(LearningGoal, goal_id)
    if goal is None:
        return None
    if title is not None:
        goal.title = title
    if description is not None:
        goal.description = description
    if target_date is not None:
        goal.target_date = target_date
    if is_completed is not None:
        goal.is_completed = is_completed
        if is_completed:
            goal.completed_at = _utcnow()
    goal.updated_at = _utcnow()
    session.add(goal)
    await session.commit()
    await session.refresh(goal)
    return goal


async def delete_learning_goal(session: AsyncSession, goal_id: uuid.UUID) -> bool:
    """Delete a learning goal."""
    goal = await session.get(LearningGoal, goal_id)
    if goal is None:
        return False
    await session.delete(goal)
    await session.commit()
    return True


# --------------------------------------------------------------------------- #
# Learner Memory helpers (delegated to academy service)
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
    """Create or update learner memory (delegated to academy service)."""
    from app.academy.service import upsert_learner_memory as _upsert
    return await _upsert(
        session,
        course_id=course_id,
        user_id=user_id,
        topic=topic,
        mastery_level=mastery_level,
        confidence=confidence,
        test_results=test_results,
        mistakes=mistakes,
        weaknesses=weaknesses,
        goals=goals,
        preferences=preferences,
        review_schedule=review_schedule,
        progress_summary=progress_summary,
    )


async def list_learner_memories(
    session: AsyncSession,
    *,
    course_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    topic: str | None = None,
) -> list[LearnerMemory]:
    """List learner memories (delegated to academy service)."""
    from app.academy.service import list_learner_memories as _list
    return await _list(session, course_id=course_id, user_id=user_id, topic=topic)


async def get_learner_memory(
    session: AsyncSession,
    course_id: uuid.UUID,
    user_id: uuid.UUID,
    topic: str,
) -> LearnerMemory | None:
    """Get learner memory (delegated to academy service)."""
    from app.academy.service import get_learner_memory as _get
    return await _get(session, course_id=course_id, user_id=user_id, topic=topic)


async def delete_learner_memory(
    session: AsyncSession,
    course_id: uuid.UUID,
    user_id: uuid.UUID,
    topic: str,
) -> bool:
    """Delete learner memory (delegated to academy service)."""
    from app.academy.service import delete_learner_memory as _delete
    return await _delete(session, course_id=course_id, user_id=user_id, topic=topic)


# --------------------------------------------------------------------------- #
# Practice Problem Service
# --------------------------------------------------------------------------- #

async def create_practice_problem(
    session: AsyncSession,
    *,
    course_id: uuid.UUID,
    problem_type: str,
    problem_statement: str,
    solution: str,
    hints: str | None = None,
    difficulty_level: int = 1,
    time_limit_minutes: int | None = None,
) -> PracticeProblem:
    """Create a practice problem."""
    problem = PracticeProblem(
        course_id=course_id,
        problem_type=problem_type,
        title=problem_statement[:100],
        problem_statement=problem_statement,
        solution=solution,
        hints=hints,
        difficulty_level=difficulty_level,
        time_limit_minutes=time_limit_minutes,
    )
    session.add(problem)
    await session.commit()
    await session.refresh(problem)
    return problem


async def list_practice_problems(
    session: AsyncSession,
    *,
    course_id: uuid.UUID | None = None,
    problem_type: str | None = None,
    difficulty_level: int | None = None,
    limit: int = 50,
) -> list[PracticeProblem]:
    """List practice problems."""
    stmt = __import__("sqlalchemy").select(PracticeProblem)
    conditions = []
    if course_id is not None:
        conditions.append(PracticeProblem.course_id == course_id)
    if problem_type is not None:
        conditions.append(PracticeProblem.problem_type == problem_type)
    if difficulty_level is not None:
        conditions.append(PracticeProblem.difficulty_level == difficulty_level)
    if conditions:
        stmt = stmt.where(__import__("sqlalchemy").or_(*conditions))
    stmt = stmt.order_by(PracticeProblem.difficulty_level.asc(), PracticeProblem.created_at.desc()).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def get_practice_problem(session: AsyncSession, problem_id: uuid.UUID) -> PracticeProblem | None:
    """Get a practice problem by ID."""
    return await session.get(PracticeProblem, problem_id)


# --------------------------------------------------------------------------- #
# Practice Attempt Service
# --------------------------------------------------------------------------- #

async def start_practice_attempt(
    session: AsyncSession,
    *,
    problem_id: uuid.UUID,
    user_id: uuid.UUID,
    course_id: uuid.UUID,
) -> PracticeAttempt:
    """Start a new practice attempt."""
    attempt = PracticeAttempt(
        problem_id=problem_id,
        user_id=user_id,
        course_id=course_id,
        status="in_progress",
    )
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)
    return attempt


async def submit_practice_attempt(
    session: AsyncSession,
    *,
    attempt_id: uuid.UUID,
    answer: str | None = None,
    is_correct: bool | None = None,
    time_spent_seconds: int | None = None,
) -> PracticeAttempt | None:
    """Submit practice attempt answers."""
    attempt = await session.get(PracticeAttempt, attempt_id)
    if attempt is None:
        return None
    attempt.answer = answer
    attempt.is_correct = is_correct
    if time_spent_seconds is not None:
        attempt.time_spent_seconds = time_spent_seconds
    attempt.completed_at = _utcnow()
    attempt.updated_at = _utcnow()
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)
    return attempt


# --------------------------------------------------------------------------- #
# Language Exercise Service
# --------------------------------------------------------------------------- #

async def create_language_exercise(
    session: AsyncSession,
    *,
    course_id: uuid.UUID,
    exercise_type: str,
    source_text: str,
    target_text: str | None = None,
    source_language: str = "en",
    target_language: str = "fa",
    difficulty_level: int = 1,
) -> LanguageExercise:
    """Create a language exercise."""
    exercise = LanguageExercise(
        course_id=course_id,
        exercise_type=exercise_type,
        source_text=source_text,
        target_text=target_text,
        source_language=source_language,
        target_language=target_language,
        difficulty_level=difficulty_level,
    )
    session.add(exercise)
    await session.commit()
    await session.refresh(exercise)
    return exercise


async def list_language_exercises(
    session: AsyncSession,
    *,
    course_id: uuid.UUID | None = None,
    exercise_type: str | None = None,
    source_language: str | None = None,
    target_language: str | None = None,
    limit: int = 50,
) -> list[LanguageExercise]:
    """List language exercises."""
    stmt = __import__("sqlalchemy").select(LanguageExercise)
    conditions = []
    if course_id is not None:
        conditions.append(LanguageExercise.course_id == course_id)
    if exercise_type is not None:
        conditions.append(LanguageExercise.exercise_type == exercise_type)
    if source_language is not None:
        conditions.append(LanguageExercise.source_language == source_language)
    if target_language is not None:
        conditions.append(LanguageExercise.target_language == target_language)
    if conditions:
        stmt = stmt.where(__import__("sqlalchemy").or_(*conditions))
    stmt = stmt.order_by(LanguageExercise.difficulty_level.asc(), LanguageExercise.created_at.desc()).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def create_language_exercise_attempt(
    session: AsyncSession,
    *,
    exercise_id: uuid.UUID,
    user_id: uuid.UUID,
    course_id: uuid.UUID,
    user_answer: str | None = None,
    is_correct: bool | None = None,
    score: float | None = None,
) -> LanguageExerciseAttempt:
    """Create a language exercise attempt."""
    attempt = LanguageExerciseAttempt(
        exercise_id=exercise_id,
        user_id=user_id,
        course_id=course_id,
        user_answer=user_answer,
        is_correct=is_correct,
        score=score,
    )
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)
    return attempt


# --------------------------------------------------------------------------- #
# Learning Analytics Service
# --------------------------------------------------------------------------- #

async def record_learning_analytics(
    session: AsyncSession,
    *,
    course_id: uuid.UUID | None,
    user_id: uuid.UUID,
    date: datetime | None = None,
    documents_read: int = 0,
    chunks_indexed: int = 0,
    lessons_completed: int = 0,
    quizzes_taken: int = 0,
    average_score: float | None = None,
    time_spent_minutes: int = 0,
    flashcards_reviewed: int = 0,
    exercises_completed: int = 0,
) -> LearningAnalytics:
    """Record analytics data for a given date."""
    if date is None:
        date = _utcnow()

    stmt = __import__("sqlalchemy").select(LearningAnalytics).where(
        LearningAnalytics.user_id == user_id,
        LearningAnalytics.course_id == course_id,
        LearningAnalytics.date == date,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()

    if existing:
        existing.documents_read = documents_read
        existing.chunks_indexed = chunks_indexed
        existing.lessons_completed = lessons_completed
        existing.quizzes_taken = quizzes_taken
        if average_score is not None:
            existing.average_score = average_score
        existing.time_spent_minutes = time_spent_minutes
        existing.flashcards_reviewed = flashcards_reviewed
        existing.exercises_completed = exercises_completed
        existing.updated_at = _utcnow()
        session.add(existing)
        await session.commit()
        await session.refresh(existing)
        return existing
    else:
        analytics = LearningAnalytics(
            course_id=course_id,
            user_id=user_id,
            date=date,
            documents_read=documents_read,
            chunks_indexed=chunks_indexed,
            lessons_completed=lessons_completed,
            quizzes_taken=quizzes_taken,
            average_score=average_score,
            time_spent_minutes=time_spent_minutes,
            flashcards_reviewed=flashcards_reviewed,
            exercises_completed=exercises_completed,
        )
        session.add(analytics)
        await session.commit()
        await session.refresh(analytics)
        return analytics


async def get_learning_analytics(
    session: AsyncSession,
    *,
    course_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[LearningAnalytics]:
    """List learning analytics records."""
    stmt = __import__("sqlalchemy").select(LearningAnalytics)
    conditions = []
    if course_id is not None:
        conditions.append(LearningAnalytics.course_id == course_id)
    if user_id is not None:
        conditions.append(LearningAnalytics.user_id == user_id)
    if start_date is not None:
        conditions.append(LearningAnalytics.date >= start_date)
    if end_date is not None:
        conditions.append(LearningAnalytics.date <= end_date)
    if conditions:
        stmt = stmt.where(__import__("sqlalchemy").or_(*conditions))
    stmt = stmt.order_by(LearningAnalytics.date.asc())
    return list((await session.execute(stmt)).scalars().all())


async def get_learning_analytics_summary(
    session: AsyncSession,
    *,
    course_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    """Get aggregated learning analytics."""
    analytics = await list_learning_analytics(
        session, course_id=course_id, user_id=user_id, start_date=start_date, end_date=end_date
    )

    total_documents = sum(a.documents_read for a in analytics)
    total_chunks = sum(a.chunks_indexed for a in analytics)
    total_lessons = sum(a.lessons_completed for a in analytics)
    total_quizzes = sum(a.quizzes_taken for a in analytics)
    total_time = sum(a.time_spent_minutes for a in analytics)
    total_flashcards = sum(a.flashcards_reviewed for a in analytics)
    total_exercises = sum(a.exercises_completed for a in analytics)

    scores = [a.average_score for a in analytics if a.average_score is not None]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    return {
        "course_id": str(course_id) if course_id else None,
        "user_id": str(user_id) if user_id else None,
        "date_range": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None,
        },
        "totals": {
            "documents_read": total_documents,
            "chunks_indexed": total_chunks,
            "lessons_completed": total_lessons,
            "quizzes_taken": total_quizzes,
            "flashcards_reviewed": total_flashcards,
            "exercises_completed": total_exercises,
            "time_spent_minutes": total_time,
        },
        "average_score": round(avg_score, 2),
        "days_active": len(analytics),
    }


# Alias for backwards compatibility with router imports
report_learning_analytics = get_learning_analytics_summary