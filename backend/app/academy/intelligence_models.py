"""Academy Intelligence models: lessons, quizzes, assessments, socratic sessions."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Index
from sqlmodel import Field, SQLModel

from app.config import settings


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LessonType(str, enum.Enum):
    INTRODUCTION = "introduction"
    CONCEPT = "concept"
    EXAMPLE = "example"
    PRACTICE = "practice"
    SUMMARY = "summary"
    REVIEW = "review"


class LessonStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class QuizType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"


class QuizStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class SocraticMode(str, enum.Enum):
    QUESTION = "question"
    HINT = "hint"
    EXPLANATION = "explanation"
    FEEDBACK = "feedback"


class Lesson(SQLModel, table=True):
    """AI-generated lesson content for a course topic."""
    __tablename__ = "lesson"
    __table_args__ = (
        Index("ix_lesson_course_id", "course_id"),
        Index("ix_lesson_topic", "topic"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", index=True)
    topic: str = Field(max_length=255, index=True)
    title: str = Field(max_length=500)
    content: str = Field(max_length=50000)  # Full lesson text
    lesson_type: LessonType = Field(default=LessonType.CONCEPT)
    status: LessonStatus = Field(default=LessonStatus.DRAFT)
    order_index: int = Field(default=0)  # Order within course
    estimated_minutes: int | None = Field(default=None)
    ai_generated: bool = Field(default=True)
    generation_prompt: str | None = Field(default=None, max_length=5000)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    

class LessonQuizLink(SQLModel, table=True):
    """Links a lesson to its assessment quiz."""
    __tablename__ = "lessonquizlink"

    lesson_id: uuid.UUID = Field(foreign_key="lesson.id", primary_key=True)
    quiz_id: uuid.UUID = Field(foreign_key="quiz.id", primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow)


class Quiz(SQLModel, table=True):
    """Quiz/assessment for a lesson or course."""
    __tablename__ = "quiz"
    __table_args__ = (
        Index("ix_quiz_course_id", "course_id"),
        Index("ix_quiz_topic", "topic"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", index=True)
    topic: str = Field(max_length=255, index=True)
    title: str = Field(max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    quiz_type: QuizType = Field(default=QuizType.MULTIPLE_CHOICE)
    status: QuizStatus = Field(default=QuizStatus.DRAFT)
    time_limit_minutes: int | None = Field(default=None)
    passing_score: float = Field(default=0.7, ge=0.0, le=1.0)
    ai_generated: bool = Field(default=True)
    generation_prompt: str | None = Field(default=None, max_length=5000)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    

class QuizQuestion(SQLModel, table=True):
    """Individual question within a quiz."""
    __tablename__ = "quizquestion"
    __table_args__ = (
        Index("ix_quizquestion_quiz_id", "quiz_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    quiz_id: uuid.UUID = Field(foreign_key="quiz.id", index=True)
    question_text: str = Field(max_length=5000)
    question_type: QuizType = Field(default=QuizType.MULTIPLE_CHOICE)
    options: str | None = Field(default=None, max_length=10000)  # JSON array for MC options
    correct_answer: str = Field(max_length=5000)
    explanation: str | None = Field(default=None, max_length=5000)
    points: float = Field(default=1.0, ge=0.0)
    order_index: int = Field(default=0)
    ai_generated: bool = Field(default=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class QuizAttempt(SQLModel, table=True):
    """User's attempt at a quiz."""
    __tablename__ = "quizattempt"
    __table_args__ = (
        Index("ix_quizattempt_quiz_id", "quiz_id"),
        Index("ix_quizattempt_user_id", "user_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    quiz_id: uuid.UUID = Field(foreign_key="quiz.id", index=True)
    user_id: uuid.UUID = Field(index=True)
    course_id: uuid.UUID = Field(index=True)
    status: AttemptStatus = Field(default=AttemptStatus.IN_PROGRESS)
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    points_earned: float = Field(default=0.0)
    points_total: float = Field(default=0.0)
    answers: str | None = Field(default=None, max_length=50000)  # JSON of user answers
    started_at: datetime = Field(default_factory=_utcnow)
    completed_at: datetime | None = Field(default=None)
    updated_at: datetime = Field(default_factory=_utcnow)


class LessonUserProgress(SQLModel, table=True):
    """User's progress through a specific lesson."""
    __tablename__ = "lessonuserprogress"
    __table_args__ = (
        Index("ix_lessonuserprogress_lesson_id", "lesson_id"),
        Index("ix_lessonuserprogress_user_id", "user_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    lesson_id: uuid.UUID = Field(foreign_key="lesson.id", index=True)
    user_id: uuid.UUID = Field(index=True)
    course_id: uuid.UUID = Field(index=True)
    status: LessonStatus = Field(default=LessonStatus.DRAFT)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    time_spent_minutes: int = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=10000)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class SocraticSession(SQLModel, table=True):
    """Socratic tutoring session - question-based dialogue."""
    __tablename__ = "socraticsession"
    __table_args__ = (
        Index("ix_socraticsession_course_id", "course_id"),
        Index("ix_socraticsession_user_id", "user_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", index=True)
    user_id: uuid.UUID = Field(index=True)
    topic: str = Field(max_length=255, index=True)
    mode: SocraticMode = Field(default=SocraticMode.QUESTION)
    messages: str | None = Field(default=None, max_length=100000)  # JSON array of messages
    current_question: str | None = Field(default=None, max_length=5000)
    hints_given: int = Field(default=0, ge=0)
    explanations_given: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


# Import enum at module level for SQLAlchemy
Lesson.model_rebuild()
LessonQuizLink.model_rebuild()
Quiz.model_rebuild()
QuizQuestion.model_rebuild()
QuizAttempt.model_rebuild()
LessonUserProgress.model_rebuild()
SocraticSession.model_rebuild()
