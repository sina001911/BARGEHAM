"""Academy Learning Tools tables: flashcards, study sessions, learner memory, practice problems, language exercises, analytics.

Revision ID: 0007_academy_learning
Revises: 0006_academy_intelligence
Create Date: 2026-11-25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0007_academy_learning"
down_revision = "0006_academy_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Flashcard table
    op.create_table(
        "flashcard",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("front", sa.String(length=5000), nullable=False),
        sa.Column("back", sa.String(length=5000), nullable=False),
        sa.Column(
            "card_type",
            sa.String(length=50),
            nullable=False,
            server_default="text",
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="new",
        ),
        sa.Column("ease_factor", sa.Float(), nullable=False, server_default="2.5"),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("repetitions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_reviewed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_review", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"], ["course.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_flashcard_course_id"), "flashcard", ["course_id"])
    op.create_index(op.f("ix_flashcard_user_id"), "flashcard", ["user_id"])
    op.create_index(op.f("ix_flashcard_status"), "flashcard", ["status"])

    # Flashcard review table
    op.create_table(
        "flashcard_review",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("card_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quality", sa.Integer(), nullable=False),
        sa.Column("response_time_seconds", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["card_id"], ["flashcard.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_flashcard_review_card_id"), "flashcard_review", ["card_id"])
    op.create_index(op.f("ix_flashcard_review_user_id"), "flashcard_review", ["user_id"])
    op.create_index(
        op.f("ix_flashcard_review_reviewed_at"),
        "flashcard_review",
        ["reviewed_at"],
    )

    # Study session table
    op.create_table(
        "study_session",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "session_type",
            sa.String(length=50),
            nullable=False,
            server_default="study",
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("items_studied", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_correct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.String(length=5000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"], ["course.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_study_session_user_id"), "study_session", ["user_id"])
    op.create_index(
        op.f("ix_study_session_course_id"), "study_session", ["course_id"]
    )
    op.create_index(
        op.f("ix_study_session_started_at"), "study_session", ["started_at"]
    )

    # Learning goal table
    op.create_table(
        "learning_goal",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("target_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"], ["course.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_goal_user_id"), "learning_goal", ["user_id"])
    op.create_index(op.f("ix_learning_goal_course_id"), "learning_goal", ["course_id"])
    op.create_index(
        op.f("ix_learning_goal_target_date"), "learning_goal", ["target_date"]
    )

    # Practice problem table
    op.create_table(
        "practice_problem",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("problem_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("problem_statement", sa.String(length=10000), nullable=False),
        sa.Column("solution", sa.String(length=10000), nullable=False),
        sa.Column("hints", sa.String(length=5000), nullable=True),
        sa.Column("difficulty_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("time_limit_minutes", sa.Integer(), nullable=True),
        sa.Column("ai_generated", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("generation_prompt", sa.String(length=5000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"], ["course.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_practice_problem_course_id"), "practice_problem", ["course_id"])
    op.create_index(
        op.f("ix_practice_problem_problem_type"), "practice_problem", ["problem_type"]
    )

    # Practice attempt table
    op.create_table(
        "practice_attempt",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("problem_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answer", sa.String(length=10000), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["problem_id"], ["practice_problem.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_practice_attempt_problem_id"), "practice_attempt", ["problem_id"])
    op.create_index(
        op.f("ix_practice_attempt_user_id"), "practice_attempt", ["user_id"]
    )

    # Language exercise table
    op.create_table(
        "language_exercise",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exercise_type", sa.String(length=50), nullable=False),
        sa.Column("source_text", sa.String(length=5000), nullable=False),
        sa.Column("target_text", sa.String(length=5000), nullable=True),
        sa.Column("source_language", sa.String(length=10), nullable=False),
        sa.Column("target_language", sa.String(length=10), nullable=False),
        sa.Column("difficulty_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("ai_generated", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("generation_prompt", sa.String(length=5000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"], ["course.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_language_exercise_course_id"), "language_exercise", ["course_id"])
    op.create_index(
        op.f("ix_language_exercise_exercise_type"), "language_exercise", ["exercise_type"]
    )

    # Language exercise attempt table
    op.create_table(
        "language_exercise_attempt",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exercise_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_answer", sa.String(length=5000), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["exercise_id"], ["language_exercise.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_language_exercise_attempt_exercise_id"),
        "language_exercise_attempt",
        ["exercise_id"],
    )
    op.create_index(
        op.f("ix_language_exercise_attempt_user_id"),
        "language_exercise_attempt",
        ["user_id"],
    )

    # Learning analytics table
    op.create_table(
        "learning_analytics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("documents_read", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunks_indexed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lessons_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quizzes_taken", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("time_spent_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("flashcards_reviewed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("exercises_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"], ["course.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_analytics_user_id"), "learning_analytics", ["user_id"])
    op.create_index(
        op.f("ix_learning_analytics_course_id"), "learning_analytics", ["course_id"]
    )
    op.create_index(
        op.f("ix_learning_analytics_date"), "learning_analytics", ["date"]
    )


def downgrade() -> None:
    op.drop_table("learning_analytics")
    op.drop_table("language_exercise_attempt")
    op.drop_table("language_exercise")
    op.drop_index(op.f("ix_practice_attempt_user_id"), table_name="practice_attempt")
    op.drop_index(op.f("ix_practice_attempt_problem_id"), table_name="practice_attempt")
    op.drop_table("practice_attempt")
    op.drop_index(op.f("ix_practice_problem_problem_type"), table_name="practice_problem")
    op.drop_index(op.f("ix_practice_problem_course_id"), table_name="practice_problem")
    op.drop_table("practice_problem")
    op.drop_index(op.f("ix_learning_goal_user_id"), table_name="learning_goal")
    op.drop_index(op.f("ix_learning_goal_course_id"), table_name="learning_goal")
    op.drop_index(op.f("ix_learning_goal_target_date"), table_name="learning_goal")
    op.drop_table("learning_goal")
    op.drop_index(op.f("ix_study_session_user_id"), table_name="study_session")
    op.drop_index(op.f("ix_study_session_course_id"), table_name="study_session")
    op.drop_index(op.f("ix_study_session_started_at"), table_name="study_session")
    op.drop_table("study_session")
    op.drop_index(op.f("ix_flashcard_review_user_id"), table_name="flashcard_review")
    op.drop_index(op.f("ix_flashcard_review_card_id"), table_name="flashcard_review")
    op.drop_table("flashcard_review")
    op.drop_index(op.f("ix_flashcard_status"), table_name="flashcard")
    op.drop_index(op.f("ix_flashcard_user_id"), table_name="flashcard")
    op.drop_index(op.f("ix_flashcard_course_id"), table_name="flashcard")
    op.drop_table("flashcard")