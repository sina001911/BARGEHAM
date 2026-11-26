"""Academy Foundation tables: course, coursefolderlink, learnermemory, courseprogress.

Revision ID: 0005_academy_foundation
Revises: 0004_knowledge_engine
Create Date: 2026-11-25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0005_academy_foundation"
down_revision = "0004_knowledge_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Courses table
    op.create_table(
        "course",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column(
            "course_type",
            sa.String(length=50),
            nullable=False,
            server_default="personal",
        ),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "embedding_model", sa.String(length=255), nullable=False, server_default=""
        ),
        sa.Column("embedding_dim", sa.Integer(), nullable=False, server_default="1024"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_course_name"), "course", ["name"])
    op.create_index(op.f("ix_course_owner_id"), "course", ["owner_id"])

    # Course-folder links
    op.create_table(
        "coursefolderlink",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("folder_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("folder_path", sa.String(length=2000), nullable=False),
        sa.Column(
            "watch_enabled", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_indexed", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["course_id"], ["course.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_coursefolderlink_folder_id"), "coursefolderlink", ["folder_id"]
    )
    op.create_index(
        op.f("ix_coursefolderlink_course_id"), "coursefolderlink", ["course_id"]
    )

    # Learner memory
    op.create_table(
        "learnermemory",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column(
            "mastery_level",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
        sa.Column(
            "confidence", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column("test_results", sa.String(length=4096), nullable=True),
        sa.Column("mistakes", sa.String(length=4096), nullable=True),
        sa.Column("weaknesses", sa.String(length=1000), nullable=True),
        sa.Column("goals", sa.String(length=1000), nullable=True),
        sa.Column("preferences", sa.String(length=1000), nullable=True),
        sa.Column(
            "review_schedule", sa.String(length=2000), nullable=True
        ),
        sa.Column(
            "progress_summary", sa.String(length=2000), nullable=True
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"], ["course.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learnermemory_course_id"), "learnermemory", ["course_id"])
    op.create_index(
        op.f("ix_learnermemory_user_id"), "learnermemory", ["user_id"]
    )
    op.create_index(op.f("ix_learnermemory_topic"), "learnermemory", ["topic"])

    # Course progress
    op.create_table(
        "courseprogress",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "documents_indexed", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "chunks_indexed", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "lessons_completed", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "quizzes_taken", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "average_score",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
        sa.Column("last_activity", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"], ["course.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_courseprogress_course_id"), "courseprogress", ["course_id"]
    )
    op.create_index(
        op.f("ix_courseprogress_user_id"), "courseprogress", ["user_id"]
    )


def downgrade() -> None:
    op.drop_table("courseprogress")
    op.drop_table("learnermemory")
    op.drop_table("coursefolderlink")
    op.drop_index(op.f("ix_course_owner_id"), table_name="course")
    op.drop_index(op.f("ix_course_name"), table_name="course")
    op.drop_table("course")
