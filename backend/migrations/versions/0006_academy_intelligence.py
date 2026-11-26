"""Academy Intelligence tables: lessons, quizzes, quiz questions, attempts, lesson progress, socratic sessions.

Revision ID: 0006_academy_intelligence
Revises: 0005_academy_foundation
Create Date: 2026-11-25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0006_academy_intelligence"
down_revision = "0005_academy_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Lessons table
    op.create_table(
        "lesson",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.String(length=50000), nullable=False),
        sa.Column(
            "lesson_type",
            sa.String(length=50),
            nullable=False,
            server_default="concept",
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True),
        sa.Column("ai_generated", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("generation_prompt", sa.String(length=5000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"], ["course.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lesson_course_id"), "lesson", ["course_id"])
    op.create_index(op.f("ix_lesson_topic"), "lesson", ["topic"])

    # Quiz table
    op.create_table(
        "quiz",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column(
            "quiz_type",
            sa.String(length=50),
            nullable=False,
            server_default="multiple_choice",
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("time_limit_minutes", sa.Integer(), nullable=True),
        sa.Column(
            "passing_score",
            sa.Float(),
            nullable=False,
            server_default="0.7",
        ),
        sa.Column("ai_generated", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("generation_prompt", sa.String(length=5000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"], ["course.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quiz_course_id"), "quiz", ["course_id"])
    op.create_index(op.f("ix_quiz_topic"), "quiz", ["topic"])

    # Quiz question table
    op.create_table(
        "quizquestion",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_text", sa.String(length=5000), nullable=False),
        sa.Column(
            "question_type",
            sa.String(length=50),
            nullable=False,
            server_default="multiple_choice",
        ),
        sa.Column("options", sa.String(length=10000), nullable=True),
        sa.Column("correct_answer", sa.String(length=5000), nullable=False),
        sa.Column("explanation", sa.String(length=5000), nullable=True),
        sa.Column("points", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ai_generated", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["quiz_id"], ["quiz.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quizquestion_quiz_id"), "quizquestion", ["quiz_id"])

    # Quiz attempt table
    op.create_table(
        "quizattempt",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="in_progress",
        ),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("points_earned", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("points_total", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("answers", sa.String(length=50000), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["quiz_id"], ["quiz.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quizattempt_quiz_id"), "quizattempt", ["quiz_id"])
    op.create_index(op.f("ix_quizattempt_user_id"), "quizattempt", ["user_id"])

    # Lesson user progress table
    op.create_table(
        "lessonuserprogress",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "time_spent_minutes",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("notes", sa.String(length=10000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["lesson_id"], ["lesson.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_lessonuserprogress_lesson_id"), "lessonuserprogress", ["lesson_id"]
    )
    op.create_index(
        op.f("ix_lessonuserprogress_user_id"), "lessonuserprogress", ["user_id"]
    )

    # Socratic session table
    op.create_table(
        "socraticsession",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column(
            "mode",
            sa.String(length=50),
            nullable=False,
            server_default="question",
        ),
        sa.Column("messages", sa.String(length=100000), nullable=True),
        sa.Column("current_question", sa.String(length=5000), nullable=True),
        sa.Column("hints_given", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "explanations_given",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"], ["course.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_socraticsession_course_id"), "socraticsession", ["course_id"]
    )
    op.create_index(
        op.f("ix_socraticsession_user_id"), "socraticsession", ["user_id"]
    )

    # Lesson-quiz link table
    op.create_table(
        "lessonquizlink",
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["lesson_id"], ["lesson.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["quiz_id"], ["quiz.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("lesson_id", "quiz_id"),
    )


def downgrade() -> None:
    op.drop_table("lessonquizlink")
    op.drop_table("socraticsession")
    op.drop_index(
        op.f("ix_lessonuserprogress_user_id"), table_name="lessonuserprogress"
    )
    op.drop_index(
        op.f("ix_lessonuserprogress_lesson_id"), table_name="lessonuserprogress"
    )
    op.drop_table("lessonuserprogress")
    op.drop_index(op.f("ix_quizattempt_user_id"), table_name="quizattempt")
    op.drop_index(op.f("ix_quizattempt_quiz_id"), table_name="quizattempt")
    op.drop_table("quizattempt")
    op.drop_index(op.f("ix_quizquestion_quiz_id"), table_name="quizquestion")
    op.drop_table("quizquestion")
    op.drop_index(op.f("ix_quiz_topic"), table_name="quiz")
    op.drop_index(op.f("ix_quiz_course_id"), table_name="quiz")
    op.drop_table("quiz")
    op.drop_index(op.f("ix_lesson_topic"), table_name="lesson")
    op.drop_index(op.f("ix_lesson_course_id"), table_name="lesson")
    op.drop_table("lesson")
