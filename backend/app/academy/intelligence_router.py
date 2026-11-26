"""Academy Intelligence API endpoints: AI Tutor, Adaptive Learning, Socratic Learning, Knowledge Assessment."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.academy import service as academy_service
from app.academy.intelligence_service import (
    generate_lesson,
    list_lessons,
    get_lesson,
    update_lesson,
    delete_lesson,
    upsert_lesson_progress,
    list_lesson_progress,
    generate_quiz,
    list_quizzes,
    get_quiz,
    get_quiz_questions,
    start_quiz_attempt,
    submit_quiz_answers,
    list_quiz_attempts,
    create_socratic_session,
    socratic_respond,
    list_socratic_sessions,
    close_socratic_session,
    get_adaptive_next_lesson,
    get_adaptive_learning_path,
)
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
    create_language_exercise,
    list_language_exercises,
    create_language_exercise_attempt,
    record_learning_analytics,
    get_learning_analytics_summary,
)
from app.academy.intelligence_models import (
    Lesson,
    LessonType,
    LessonStatus,
    Quiz,
    QuizType,
    QuizStatus,
    QuizQuestion,
    QuizAttempt,
    LessonUserProgress,
    SocraticSession,
    SocraticMode,
    AttemptStatus,
)
from app.academy.models import Course
from app.auth.router import get_current_user
from app.database import get_session
from app.users.models import User

router = APIRouter(prefix="/academy/intelligence", tags=["academy-intelligence"])

# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #

class LessonCreate(BaseModel):
    course_id: uuid.UUID
    topic: str
    title: str | None = None
    lesson_type: LessonType = LessonType.CONCEPT
    estimated_minutes: int | None = None


class LessonRead(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    topic: str
    title: str
    content: str
    lesson_type: LessonType
    status: LessonStatus
    order_index: int
    estimated_minutes: int | None = None
    ai_generated: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LessonUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    lesson_type: LessonType | None = None
    status: LessonStatus | None = None
    order_index: int | None = None
    estimated_minutes: int | None = None


class GenerateLessonRequest(BaseModel):
    course_id: uuid.UUID
    topic: str
    title: str | None = None
    lesson_type: LessonType = LessonType.CONCEPT
    estimated_minutes: int | None = None


class LessonProgressCreate(BaseModel):
    lesson_id: uuid.UUID
    user_id: uuid.UUID
    course_id: uuid.UUID
    status: str | None = None
    time_spent_minutes: int | None = None
    notes: str | None = None


class LessonProgressRead(BaseModel):
    id: uuid.UUID
    lesson_id: uuid.UUID
    user_id: uuid.UUID
    course_id: uuid.UUID
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    time_spent_minutes: int
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuizCreate(BaseModel):
    course_id: uuid.UUID
    topic: str
    title: str | None = None
    quiz_type: QuizType = QuizType.MULTIPLE_CHOICE
    time_limit_minutes: int | None = None
    passing_score: float = 0.7
    num_questions: int = 5


class QuizRead(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    topic: str
    title: str
    description: str | None = None
    quiz_type: QuizType
    status: QuizStatus
    time_limit_minutes: int | None = None
    passing_score: float
    ai_generated: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuizQuestionRead(BaseModel):
    id: uuid.UUID
    quiz_id: uuid.UUID
    question_text: str
    question_type: QuizType
    options: str | None = None
    correct_answer: str
    explanation: str | None = None
    points: float
    order_index: int
    ai_generated: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuizAttemptStart(BaseModel):
    quiz_id: uuid.UUID
    user_id: uuid.UUID
    course_id: uuid.UUID


class QuizAttemptRead(BaseModel):
    id: uuid.UUID
    quiz_id: uuid.UUID
    user_id: uuid.UUID
    course_id: uuid.UUID
    status: AttemptStatus
    score: float | None = None
    points_earned: float
    points_total: float
    answers: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    updated_at: datetime

    class Config:
        from_attributes = True


class QuizAnswerSubmit(BaseModel):
    attempt_id: uuid.UUID
    answers: dict[str, str]


class SocraticSessionCreate(BaseModel):
    course_id: uuid.UUID
    user_id: uuid.UUID
    topic: str
    mode: SocraticMode = SocraticMode.QUESTION


class SocraticSessionRead(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    user_id: uuid.UUID
    topic: str
    mode: SocraticMode
    messages: str | None = None
    current_question: str | None = None
    hints_given: int
    explanations_given: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SocraticMessage(BaseModel):
    session_id: uuid.UUID
    user_message: str


class SocraticResponse(BaseModel):
    session_id: uuid.UUID
    ai_response: str
    mode: SocraticMode
    hints_given: int
    explanations_given: int
    is_active: bool


class AdaptivePathResponse(BaseModel):
    course_id: uuid.UUID
    course_name: str
    total_lessons: int
    completed_lessons: int
    overall_progress: float
    average_mastery: float
    path: list[dict]


class NextLessonResponse(BaseModel):
    next_lesson: dict | None
    reason: str


# --------------------------------------------------------------------------- #
# Lesson endpoints
# --------------------------------------------------------------------------- #

@router.post("/lessons", response_model=LessonRead, status_code=201)
async def create_lesson_endpoint(
    req: LessonCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new lesson manually."""
    course = await academy_service.get_course(session, req.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")

    lesson = await generate_lesson(
        session,
        course_id=req.course_id,
        topic=req.topic,
        title=req.title,
        lesson_type=req.lesson_type,
        estimated_minutes=req.estimated_minutes,
        user_id=current_user.id,
    )
    return lesson


@router.post("/lessons/generate", response_model=LessonRead, status_code=201)
async def generate_lesson_endpoint(
    req: GenerateLessonRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """AI-generate a lesson for a course topic."""
    course = await academy_service.get_course(session, req.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")

    lesson = await generate_lesson(
        session,
        course_id=req.course_id,
        topic=req.topic,
        title=req.title,
        lesson_type=req.lesson_type,
        estimated_minutes=req.estimated_minutes,
        user_id=current_user.id,
    )
    return lesson


@router.get("/lessons", response_model=list[LessonRead])
async def list_lessons_endpoint(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    course_id: uuid.UUID | None = Query(default=None),
    status: LessonStatus | None = Query(default=None),
    lesson_type: LessonType | None = Query(default=None),
):
    """List lessons."""
    return await list_lessons(session, course_id=course_id, status=status, lesson_type=lesson_type)


@router.get("/lessons/{lesson_id}", response_model=LessonRead)
async def get_lesson_endpoint(
    lesson_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a lesson by ID."""
    lesson = await get_lesson(session, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.patch("/lessons/{lesson_id}", response_model=LessonRead)
async def update_lesson_endpoint(
    lesson_id: uuid.UUID,
    req: LessonUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update a lesson."""
    lesson = await get_lesson(session, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    course = await academy_service.get_course(session, lesson.course_id)
    if course is None or course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")

    updated = await update_lesson(
        session,
        lesson_id,
        title=req.title,
        content=req.content,
        lesson_type=req.lesson_type,
        status=req.status,
        order_index=req.order_index,
        estimated_minutes=req.estimated_minutes,
    )
    return updated


@router.delete("/lessons/{lesson_id}", status_code=204)
async def delete_lesson_endpoint(
    lesson_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a lesson."""
    lesson = await get_lesson(session, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    course = await academy_service.get_course(session, lesson.course_id)
    if course is None or course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")
    ok = await delete_lesson(session, lesson_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Lesson not found")


# --------------------------------------------------------------------------- #
# Lesson Progress endpoints
# --------------------------------------------------------------------------- #

@router.post("/lesson-progress", response_model=LessonProgressRead, status_code=201)
async def upsert_lesson_progress_endpoint(
    req: LessonProgressCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create or update lesson progress."""
    progress = await upsert_lesson_progress(
        session,
        lesson_id=req.lesson_id,
        user_id=req.user_id,
        course_id=req.course_id,
        status=req.status,
        time_spent_minutes=req.time_spent_minutes,
        notes=req.notes,
    )
    return progress


@router.get("/lesson-progress", response_model=list[LessonProgressRead])
async def list_lesson_progress_endpoint(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    lesson_id: uuid.UUID | None = Query(default=None),
    course_id: uuid.UUID | None = Query(default=None),
):
    """List lesson progress records."""
    return await list_lesson_progress(
        session, lesson_id=lesson_id, user_id=current_user.id, course_id=course_id
    )


# --------------------------------------------------------------------------- #
# Quiz endpoints
# --------------------------------------------------------------------------- #

@router.post("/quizzes", response_model=QuizRead, status_code=201)
async def create_quiz_endpoint(
    req: QuizCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """AI-generate a quiz for a course topic."""
    course = await academy_service.get_course(session, req.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")

    quiz = await generate_quiz(
        session,
        course_id=req.course_id,
        topic=req.topic,
        title=req.title,
        quiz_type=req.quiz_type,
        time_limit_minutes=req.time_limit_minutes,
        passing_score=req.passing_score,
        num_questions=req.num_questions,
        user_id=current_user.id,
    )
    return quiz


@router.get("/quizzes", response_model=list[QuizRead])
async def list_quizzes_endpoint(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    course_id: uuid.UUID | None = Query(default=None),
    status: QuizStatus | None = Query(default=None),
):
    """List quizzes."""
    return await list_quizzes(session, course_id=course_id, status=status)


@router.get("/quizzes/{quiz_id}", response_model=QuizRead)
async def get_quiz_endpoint(
    quiz_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a quiz by ID."""
    quiz = await get_quiz(session, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


@router.get("/quizzes/{quiz_id}/questions", response_model=list[QuizQuestionRead])
async def get_quiz_questions_endpoint(
    quiz_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get all questions for a quiz."""
    return await get_quiz_questions(session, quiz_id)


# --------------------------------------------------------------------------- #
# Quiz Attempt endpoints
# --------------------------------------------------------------------------- #

@router.post("/quiz-attempts", response_model=QuizAttemptRead, status_code=201)
async def start_quiz_attempt_endpoint(
    req: QuizAttemptStart,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Start a new quiz attempt."""
    attempt = await start_quiz_attempt(
        session,
        quiz_id=req.quiz_id,
        user_id=req.user_id,
        course_id=req.course_id,
    )
    return attempt


@router.post("/quiz-attempts/{attempt_id}/submit", response_model=QuizAttemptRead)
async def submit_quiz_answers_endpoint(
    attempt_id: uuid.UUID,
    req: QuizAnswerSubmit,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Submit quiz answers and get score."""
    attempt = await submit_quiz_answers(
        session,
        attempt_id=attempt_id,
        answers=req.answers,
    )
    return attempt


@router.get("/quiz-attempts", response_model=list[QuizAttemptRead])
async def list_quiz_attempts_endpoint(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    quiz_id: uuid.UUID | None = Query(default=None),
    course_id: uuid.UUID | None = Query(default=None),
):
    """List quiz attempts for the current user."""
    return await list_quiz_attempts(
        session, quiz_id=quiz_id, user_id=current_user.id, course_id=course_id
    )


# --------------------------------------------------------------------------- #
# Socratic Learning endpoints
# --------------------------------------------------------------------------- #

@router.post("/socratic/sessions", response_model=SocraticSessionRead, status_code=201)
async def create_socratic_session_endpoint(
    req: SocraticSessionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new Socratic tutoring session."""
    course = await academy_service.get_course(session, req.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not course owner")

    socratic = await create_socratic_session(
        session,
        course_id=req.course_id,
        user_id=req.user_id,
        topic=req.topic,
        mode=req.mode,
    )
    return socratic


@router.post("/socratic/sessions/{session_id}/respond", response_model=SocraticResponse)
async def socratic_respond_endpoint(
    session_id: uuid.UUID,
    req: SocraticMessage,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Send a message in a Socratic session and get AI response."""
    result = await socratic_respond(
        session,
        session_id=session_id,
        user_message=req.user_message,
    )
    return result


@router.get("/socratic/sessions", response_model=list[SocraticSessionRead])
async def list_socratic_sessions_endpoint(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    course_id: uuid.UUID | None = Query(default=None),
    is_active: bool | None = Query(default=True),
):
    """List Socratic sessions."""
    return await list_socratic_sessions(
        session,
        course_id=course_id,
        user_id=current_user.id,
        is_active=is_active,
    )


@router.post("/socratic/sessions/{session_id}/close", response_model=SocraticSessionRead)
async def close_socratic_session_endpoint(
    session_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Close a Socratic session."""
    socratic = await close_socratic_session(session, session_id=session_id)
    if socratic is None:
        raise HTTPException(status_code=404, detail="Socratic session not found")
    return socratic


# --------------------------------------------------------------------------- #
# Adaptive Learning endpoints
# --------------------------------------------------------------------------- #

@router.get("/adaptive/next-lesson", response_model=NextLessonResponse)
async def get_adaptive_next_lesson_endpoint(
    course_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get the next recommended lesson for a user based on mastery and progress."""
    result = await get_adaptive_next_lesson(
        session,
        course_id=course_id,
        user_id=current_user.id,
    )
    return result


@router.get("/adaptive/learning-path", response_model=AdaptivePathResponse)
async def get_adaptive_learning_path_endpoint(
    course_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get the full adaptive learning path for a user in a course."""
    result = await get_adaptive_learning_path(
        session, course_id=course_id, user_id=current_user.id
    )
    return result