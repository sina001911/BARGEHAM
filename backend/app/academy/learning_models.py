"""Academy Learning Tools models: flashcards, spaced repetition, practice, language learning, study planner, analytics."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from sqlalchemy import Column, Index, ForeignKey
from sqlalchemy.dialects import postgresql
from sqlmodel import Field, SQLModel, Relationship

from app.config import settings


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FlashcardType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    CLOZE = "cloze"  # fill-in-the-blank


class FlashcardStatus(str, enum.Enum):
    NEW = "new"
    LEARNING = "learning"
    REVIEWING = "reviewing"
    MASTERED = "mastered"
    FORGOTTEN = "forgotten"


class StudySessionType(str, enum.Enum):
    STUDY = "study"
    REVIEW = "review"
    PRACTICE = "practice"
    EXAM = "exam"


class ExerciseType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    PROBLEM_SOLVING = "problem_solving"
    TRANSLATION = "translation"
    PRONUNCIATION = "pronunciation"


class PracticeProblemType(str, enum.Enum):
    MATH = "math"
    SCIENCE = "science"
    LOGIC = "logic"
    PROGRAMMING = "programming"
    LOGIC_PUZZLE = "logic_puzzle"
    WORD_PROBLEM = "word_problem"


class Flashcard(SQLModel, table=True):
    """Flashcard for spaced repetition learning."""
    __tablename__ = "flashcard"
    __table_args__ = (
        Index("ix_flashcard_course_id", "course_id"),
        Index("ix_flashcard_user_id", "user_id"),
        Index("ix_flashcard_status", "status"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", index=True)
    user_id: uuid.UUID = Field(index=True)
    front: str = Field(max_length=5000)  # Question/front content
    back: str = Field(max_length=5000)  # Answer/back content
    card_type: FlashcardType = Field(default=FlashcardType.TEXT)
    status: FlashcardStatus = Field(default=FlashcardStatus.NEW)
    ease_factor: float = Field(default=2.5)  # SM-2 ease factor
    interval_days: int = Field(default=0)  # Days until next review
    repetitions: int = Field(default=0)  # Number of successful reviews
    last_reviewed: datetime | None = Field(default=None)
    next_review: datetime | None = Field(default=None)  # Next review date
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class FlashcardReview(SQLModel, table=True):
    """Flashcard review history for spaced repetition tracking."""
    __tablename__ = "flashcard_review"
    __table_args__ = (
        Index("ix_flashcard_review_card_id", "card_id"),
        Index("ix_flashcard_review_user_id", "user_id"),
        Index("ix_flashcard_review_reviewed_at", "reviewed_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    card_id: uuid.UUID = Field(foreign_key="flashcard.id", index=True)
    user_id: uuid.UUID = Field(index=True)
    quality: int = Field(ge=0, le=5)  # SM-2 quality rating (0-5)
    response_time_seconds: int | None = Field(default=None)
    reviewed_at: datetime = Field(default_factory=_utcnow)


class StudySession(SQLModel, table=True):
    """Study session tracking."""
    __tablename__ = "study_session"
    __table_args__ = (
        Index("ix_study_session_user_id", "user_id"),
        Index("ix_study_session_course_id", "course_id"),
        Index("ix_study_session_started_at", "started_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID | None = Field(foreign_key="course.id", index=True)
    user_id: uuid.UUID = Field(index=True)
    session_type: StudySessionType = Field(default=StudySessionType.STUDY)
    started_at: datetime = Field(default_factory=_utcnow)
    ended_at: datetime | None = Field(default=None)
    duration_minutes: int | None = Field(default=None)
    items_studied: int = Field(default=0)
    items_correct: int = Field(default=0)
    notes: str | None = Field(default=None, max_length=5000)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class LearningGoal(SQLModel, table=True):
    """Learning goal for a user in a course."""
    __tablename__ = "learning_goal"
    __table_args__ = (
        Index("ix_learning_goal_user_id", "user_id"),
        Index("ix_learning_goal_course_id", "course_id"),
        Index("ix_learning_goal_target_date", "target_date"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", index=True)
    user_id: uuid.UUID = Field(index=True)
    title: str = Field(max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    target_date: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    is_completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class PracticeProblem(SQLModel, table=True):
    """Practice problem for problem-solving practice."""
    __tablename__ = "practice_problem"
    __table_args__ = (
        Index("ix_practice_problem_course_id", "course_id"),
        Index("ix_practice_problem_type", "problem_type"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", index=True)
    problem_type: PracticeProblemType = Field(default=PracticeProblemType.MATH)
    title: str = Field(max_length=500)
    problem_statement: str = Field(max_length=10000)
    solution: str = Field(max_length=10000)
    hints: str | None = Field(default=None, max_length=5000)
    difficulty_level: int = Field(default=1, ge=1, le=5)  # 1-5 difficulty
    time_limit_minutes: int | None = Field(default=None)
    ai_generated: bool = Field(default=True)
    generation_prompt: str | None = Field(default=None, max_length=5000)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class PracticeAttempt(SQLModel, table=True):
    """Practice problem attempt."""
    __tablename__ = "practice_attempt"
    __table_args__ = (
        Index("ix_practice_attempt_problem_id", "problem_id"),
        Index("ix_practice_attempt_user_id", "user_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    problem_id: uuid.UUID = Field(foreign_key="practice_problem.id", index=True)
    user_id: uuid.UUID = Field(index=True)
    course_id: uuid.UUID = Field(index=True)
    answer: str | None = Field(default=None, max_length=10000)
    is_correct: bool = Field(default=False)
    time_spent_seconds: int | None = Field(default=None)
    started_at: datetime = Field(default_factory=_utcnow)
    completed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class LanguageExercise(SQLModel, table=True):
    """Language learning exercise."""
    __tablename__ = "language_exercise"
    __table_args__ = (
        Index("ix_language_exercise_course_id", "course_id"),
        Index("ix_language_exercise_exercise_type", "exercise_type"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", index=True)
    exercise_type: ExerciseType = Field(default=ExerciseType.TRANSLATION)
    source_text: str = Field(max_length=5000)
    target_text: str | None = Field(default=None, max_length=5000)
    source_language: str = Field(max_length=10, default="en")
    target_language: str = Field(max_length=10, default="fa")
    difficulty_level: int = Field(default=1, ge=1, le=5)
    ai_generated: bool = Field(default=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class LanguageExerciseAttempt(SQLModel, table=True):
    """Language exercise attempt."""
    __tablename__ = "language_exercise_attempt"
    __table_args__ = (
        Index("ix_language_exercise_attempt_exercise_id", "exercise_id"),
        Index("ix_language_exercise_attempt_user_id", "user_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    exercise_id: uuid.UUID = Field(foreign_key="language_exercise.id", index=True)
    user_id: uuid.UUID = Field(index=True)
    course_id: uuid.UUID = Field(index=True)
    user_answer: str | None = Field(default=None, max_length=5000)
    is_correct: bool = Field(default=False)
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    started_at: datetime = Field(default_factory=_utcnow)
    completed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class LearningAnalytics(SQLModel, table=True):
    """Learning analytics and analytics data."""
    __tablename__ = "learning_analytics"
    __table_args__ = (
        Index("ix_learning_analytics_user_id", "user_id"),
        Index("ix_learning_analytics_course_id", "course_id"),
        Index("ix_learning_analytics_date", "date"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID | None = Field(foreign_key="course.id", index=True)
    user_id: uuid.UUID = Field(index=True)
    date: datetime = Field(default_factory=_utcnow)  # Date for analytics
    documents_read: int = Field(default=0)
    chunks_indexed: int = Field(default=0)
    lessons_completed: int = Field(default=0)
    quizzes_taken: int = Field(default=0)
    average_score: float = Field(default=0.0, ge=0.0, le=1.0)
    time_spent_minutes: int = Field(default=0)
    flashcards_reviewed: int = Field(default=0)
    exercises_completed: int = Field(default=0)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)