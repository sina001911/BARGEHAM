"""Academy Learning Tools API endpoints: flashcards, study sessions, learning goals, practice, language exercises, analytics."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.academy import service as academy_service
from app.academy.learning_service import (
    create_flashcard,
    list_flashcards,
    get_flashcard,
    update_flashcard,
    delete_flashcard,
    create_study_session,
    end_study_session,
    list_study_sessions,
    create_learning_goal,
    list_learning_goals,
    get_learning_goal,
    update_learning_goal,
    delete_learning_goal,
    create_practice_problem,
    list_practice_problems,
    get_practice_problem,
    start_practice_attempt,
    submit_practice_attempt,
    create_language_exercise,
    list_language_exercises,
    create_language_exercise_attempt,
    upsert_learner_memory,
    list_learner_memories,
    get_learner_memory,
    delete_learner_memory,
    report_learning_analytics,
)
from app.academy.learning_models import (
    Flashcard,
    FlashcardReview,
    LanguageExercise,
    LanguageExerciseAttempt,
    LearningGoal,
    PracticeAttempt,
    PracticeProblem,
    StudySession,
)
from app.academy.models import Course
from app.auth.router import get_current_user
from app.database import get_session
from app.users.models import User

router = APIRouter(prefix="/academy/learning", tags=["academy-learning"])

# --------------------------------------------------------------------------- #
# Flashcard endpoints
# --------------------------------------------------------------------------- #

class FlashcardCreate(BaseModel):
    course_id: uuid.UUID
    front: str
    back: str
    card_type: str = "text"


class FlashcardUpdate(BaseModel):
    front: str | None = None
    back: str | None = None
    card_type: str | None = None
    status: str | None = None
    interval_days: int | None = None
    repetitions: int | None = None
    next_review: datetime | None = None


class FlashcardRead(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    user_id: uuid.UUID
    front: str
    back: str
    card_type: str
    status: str
    ease_factor: float
    interval_days: int
    repetitions: int
    last_review: datetime | None = None
    next_review: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/flashcards", response_model=FlashcardRead, status_code=201)
async def create_flashcard_endpoint(
    req: FlashcardCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new flashcard."""
    card = await create_flashcard(
        session,
        course_id=req.course_id,
        user_id=current_user.id,
        front=req.front,
        back=req.back,
        card_type=req.card_type,
    )
    return card


@router.get("/flashcards", response_model=list[FlashcardRead])
async def list_flashcards_endpoint(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    course_id: uuid.UUID | None = Query(default=None),
    card_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50),
):
    """List flashcards for the current user."""
    return await list_flashcards(
        session,
        course_id=course_id,
        user_id=current_user.id,
        card_type=card_type,
        status=status,
        limit=limit,
    )


@router.get("/flashcards/{card_id}", response_model=FlashcardRead)
async def get_flashcard_endpoint(
    card_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a flashcard by ID."""
    card = await get_flashcard(session, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    if card.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not card owner")
    return card


@router.patch("/flashcards/{card_id}", response_model=FlashcardRead)
async def update_flashcard_endpoint(
    card_id: uuid.UUID,
    req: FlashcardUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update a flashcard."""
    card = await get_flashcard(session, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    if card.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not card owner")

    updated = await update_flashcard(
        session,
        card_id=card_id,
        front=req.front,
        back=req.back,
        card_type=req.card_type,
        status=req.status,
        interval_days=req.interval_days,
        repetitions=req.repetitions,
        next_review=req.next_review,
    )
    return updated


@router.delete("/flashcards/{card_id}", status_code=204)
async def delete_flashcard_endpoint(
    card_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a flashcard."""
    ok = await delete_flashcard(session, card_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Flashcard not found")


# --------------------------------------------------------------------------- #
# Study Session endpoints
# --------------------------------------------------------------------------- #

class StudySessionCreate(BaseModel):
    course_id: uuid.UUID | None = None
    session_type: str = "study"


class StudySessionUpdate(BaseModel):
    duration_minutes: int | None = None
    items_studied: int | None = None
    items_correct: int | None = None
    notes: str | None = None


class StudySessionRead(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID | None
    user_id: uuid.UUID
    session_type: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_minutes: int | None = None
    items_studied: int
    items_correct: int
    notes: str | None = None

    class Config:
        from_attributes = True


@router.post("/study-sessions", response_model=StudySessionRead, status_code=201)
async def create_study_session_endpoint(
    req: StudySessionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new study session."""
    session_obj = await create_study_session(
        session,
        course_id=req.course_id,
        user_id=current_user.id,
        session_type=req.session_type,
    )
    return session_obj


@router.get("/study-sessions", response_model=list[StudySessionRead])
async def list_study_sessions_endpoint(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    course_id: uuid.UUID | None = Query(default=None),
    session_type: str | None = Query(default=None),
    limit: int = Query(default=50),
):
    """List study sessions."""
    return await list_study_sessions(
        session,
        user_id=current_user.id,
        course_id=course_id,
        session_type=session_type,
        limit=limit,
    )


@router.get("/study-sessions/{session_id}", response_model=StudySessionRead)
async def get_study_session_endpoint(
    session_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a study session by ID."""
    study_session = await session.get(StudySession, session_id)
    if study_session is None:
        raise HTTPException(status_code=404, detail="Study session not found")
    if study_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not session owner")
    return study_session


@router.patch("/study-sessions/{session_id}", response_model=StudySessionRead)
async def update_study_session_endpoint(
    session_id: uuid.UUID,
    req: StudySessionUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """End a study session."""
    study_session = await end_study_session(
        session,
        session_id=session_id,
        duration_minutes=req.duration_minutes,
        items_studied=req.items_studied,
        items_correct=req.items_correct,
        notes=req.notes,
    )
    if study_session is None:
        raise HTTPException(status_code=404, detail="Study session not found")
    return study_session


# --------------------------------------------------------------------------- #
# Learning Goal endpoints
# --------------------------------------------------------------------------- #

class LearningGoalCreate(BaseModel):
    course_id: uuid.UUID
    title: str
    description: str | None = None
    target_date: datetime | None = None


class LearningGoalRead(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: str | None = None
    target_date: datetime | None = None
    completed_at: datetime | None = None
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LearningGoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    target_date: datetime | None = None
    is_completed: bool | None = None


@router.post("/learning-goals", response_model=LearningGoalRead, status_code=201)
async def create_learning_goal_endpoint(
    req: LearningGoalCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new learning goal."""
    goal = await create_learning_goal(
        session,
        course_id=req.course_id,
        user_id=current_user.id,
        title=req.title,
        description=req.description,
        target_date=req.target_date,
    )
    return goal


@router.get("/learning-goals", response_model=list[LearningGoalRead])
async def list_learning_goals_endpoint(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    course_id: uuid.UUID | None = Query(default=None),
    is_completed: bool | None = Query(default=None),
):
    """List learning goals."""
    return await list_learning_goals(
        session,
        user_id=current_user.id,
        course_id=course_id,
        is_completed=is_completed,
    )


@router.get("/learning-goals/{goal_id}", response_model=LearningGoalRead)
async def get_learning_goal_endpoint(
    goal_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a learning goal by ID."""
    goal = await get_learning_goal(session, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Learning goal not found")
    if goal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not goal owner")
    return goal


@router.patch("/learning-goals/{goal_id}", response_model=LearningGoalRead)
async def update_learning_goal_endpoint(
    goal_id: uuid.UUID,
    req: LearningGoalUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update a learning goal."""
    goal = await update_learning_goal(
        session,
        goal_id=goal_id,
        title=req.title,
        description=req.description,
        target_date=req.target_date,
        is_completed=req.is_completed,
    )
    if goal is None:
        raise HTTPException(status_code=404, detail="Learning goal not found")
    return goal


@router.delete("/learning-goals/{goal_id}", status_code=204)
async def delete_learning_goal_endpoint(
    goal_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a learning goal."""
    goal = await session.get(LearningGoal, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Learning goal not found")
    if goal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not goal owner")
    ok = await delete_learning_goal(session, goal_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Learning goal not found")


# --------------------------------------------------------------------------- #
# Practice Problem endpoints
# --------------------------------------------------------------------------- #

class PracticeProblemCreate(BaseModel):
    course_id: uuid.UUID
    problem_type: str
    problem_statement: str
    solution: str
    hints: str | None = None
    difficulty_level: int = 1
    time_limit_minutes: int | None = None


class PracticeProblemRead(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    problem_type: str
    title: str
    problem_statement: str
    solution: str
    hints: str | None = None
    difficulty_level: int
    time_limit_minutes: int | None = None
    ai_generated: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PracticeAttemptStart(BaseModel):
    problem_id: uuid.UUID
    course_id: uuid.UUID


class PracticeAttemptSubmit(BaseModel):
    user_answer: str | None = None
    is_correct: bool | None = None
    time_spent_seconds: int | None = None


class PracticeAttemptRead(BaseModel):
    id: uuid.UUID
    problem_id: uuid.UUID
    user_id: uuid.UUID
    course_id: uuid.UUID
    answer: str | None = None
    is_correct: bool
    time_spent_seconds: int | None = None
    started_at: datetime
    completed_at: datetime | None = None
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/practice-problems", response_model=PracticeProblemRead, status_code=201)
async def create_practice_problem_endpoint(
    req: PracticeProblemCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a practice problem."""
    course = await academy_service.get_course(session, req.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")

    problem = await create_practice_problem(
        session,
        course_id=req.course_id,
        problem_type=req.problem_type,
        problem_statement=req.problem_statement,
        solution=req.solution,
        hints=req.hints,
        difficulty_level=req.difficulty_level,
        time_limit_minutes=req.time_limit_minutes,
    )
    return problem


@router.get("/practice-problems", response_model=list[PracticeProblemRead])
async def list_practice_problems_endpoint(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    course_id: uuid.UUID | None = Query(default=None),
    problem_type: str | None = Query(default=None),
    difficulty_level: int | None = Query(default=None),
    limit: int = Query(default=50),
):
    """List practice problems."""
    return await list_practice_problems(
        session,
        course_id=course_id,
        problem_type=problem_type,
        difficulty_level=difficulty_level,
        limit=limit,
    )


@router.get("/practice-problems/{problem_id}", response_model=PracticeProblemRead)
async def get_practice_problem_endpoint(
    problem_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a practice problem by ID."""
    problem = await get_practice_problem(session, problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Practice problem not found")
    return problem


@router.post("/practice-attempts", response_model=PracticeAttemptRead, status_code=201)
async def start_practice_attempt_endpoint(
    req: PracticeAttemptStart,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Start a new practice attempt."""
    attempt = await start_practice_attempt(
        session,
        problem_id=req.problem_id,
        user_id=current_user.id,
        course_id=req.course_id,
    )
    return attempt


@router.post("/practice-attempts/{attempt_id}/submit", response_model=PracticeAttemptRead)
async def submit_practice_attempt_endpoint(
    attempt_id: uuid.UUID,
    req: PracticeAttemptSubmit,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Submit a practice attempt."""
    attempt = await submit_practice_attempt(
        session,
        attempt_id=attempt_id,
        answer=req.user_answer,
        is_correct=req.is_correct,
        time_spent_seconds=req.time_spent_seconds,
    )
    if attempt is None:
        raise HTTPException(status_code=404, detail="Practice attempt not found")
    return attempt


# --------------------------------------------------------------------------- #
# Language Exercise endpoints
# --------------------------------------------------------------------------- #

class LanguageExerciseCreate(BaseModel):
    course_id: uuid.UUID
    exercise_type: str
    source_text: str
    target_text: str | None = None
    source_language: str = "en"
    target_language: str = "fa"
    difficulty_level: int = 1


class LanguageExerciseRead(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    exercise_type: str
    source_text: str
    target_text: str | None = None
    source_language: str
    target_language: str
    difficulty_level: int
    ai_generated: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LanguageExerciseAttemptCreate(BaseModel):
    exercise_id: uuid.UUID
    course_id: uuid.UUID
    user_answer: str | None = None
    is_correct: bool | None = None
    score: float | None = None


class LanguageExerciseAttemptRead(BaseModel):
    id: uuid.UUID
    exercise_id: uuid.UUID
    user_id: uuid.UUID
    course_id: uuid.UUID
    user_answer: str | None = None
    is_correct: bool
    score: float | None = None
    started_at: datetime
    completed_at: datetime | None = None
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/language-exercises", response_model=LanguageExerciseRead, status_code=201)
async def create_language_exercise_endpoint(
    req: LanguageExerciseCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a language exercise."""
    course = await academy_service.get_course(session, req.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")

    exercise = await create_language_exercise(
        session,
        course_id=req.course_id,
        exercise_type=req.exercise_type,
        source_text=req.source_text,
        target_text=req.target_text,
        source_language=req.source_language,
        target_language=req.target_language,
        difficulty_level=req.difficulty_level,
    )
    return exercise


@router.get("/language-exercises", response_model=list[LanguageExerciseRead])
async def list_language_exercises_endpoint(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    course_id: uuid.UUID | None = Query(default=None),
    exercise_type: str | None = Query(default=None),
    source_language: str | None = Query(default=None),
    target_language: str | None = Query(default=None),
    limit: int = Query(default=50),
):
    """List language exercises."""
    return await list_language_exercises(
        session,
        course_id=course_id,
        exercise_type=exercise_type,
        source_language=source_language,
        target_language=target_language,
        limit=limit,
    )


@router.post("/language-exercises/{exercise_id}/attempts", response_model=LanguageExerciseAttemptRead, status_code=201)
async def create_language_exercise_attempt_endpoint(
    exercise_id: uuid.UUID,
    req: LanguageExerciseAttemptCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a language exercise attempt."""
    exercise = await session.get(LanguageExercise, exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if exercise.course_id != req.course_id:
        raise HTTPException(status_code=403, detail="Exercise not in course")
    course = await academy_service.get_course(session, req.course_id)
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")

    attempt = await create_language_exercise_attempt(
        session,
        exercise_id=exercise_id,
        user_id=current_user.id,
        course_id=req.course_id,
        user_answer=req.user_answer,
        is_correct=req.is_correct,
        score=req.score,
    )
    return attempt


# --------------------------------------------------------------------------- #
# Analytics endpoints
# --------------------------------------------------------------------------- #

class AnalyticsSummary(BaseModel):
    course_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    total_documents_read: int
    total_chunks_indexed: int
    total_lessons_completed: int
    total_quizzes_taken: int
    total_flashcards_reviewed: int
    total_exercises_completed: int
    total_time_spent_minutes: int
    average_score: float | None = None
    days_active: int


@router.get("/analytics", response_model=AnalyticsSummary)
async def get_analytics_endpoint(
    course_id: uuid.UUID | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get learning analytics."""
    return await report_learning_analytics(
        session,
        course_id=course_id,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )