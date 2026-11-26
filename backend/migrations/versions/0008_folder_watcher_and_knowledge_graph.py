"""Add folder watcher registry and knowledge graph tables.

Revision ID: 0008_folder_watcher_and_knowledge_graph
Revises: 0007_academy_learning
Create Date: 2026-11-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers
revision = "0008_folder_watcher_and_knowledge_graph"
down_revision = "0007_academy_learning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure required extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pgvector")

    # ---- Folder Watcher ----
    op.create_table(
        "folderwatcher",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("folder_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("directory_path", sa.String(length=2000), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("poll_interval_seconds", sa.Integer, server_default="10"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("items_scanned", sa.Integer, server_default="0"),
        sa.Column("items_new", sa.Integer, server_default="0"),
        sa.Column("items_updated", sa.Integer, server_default="0"),
        sa.Column("last_scan_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["folder_id"], ["folder.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("directory_path"),
    )
    op.create_index(
        op.f("ix_folderwatcher_is_active"), "folderwatcher", ["is_active"]
    )
    op.create_index(
        op.f("ix_folderwatcher_folder_id"), "folderwatcher", ["folder_id"]
    )

    # ---- Knowledge Graph — Entities ----
    op.create_table(
        "knowledge_entity",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kb_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column(
            "entity_type",
            sa.String(length=100),
            nullable=False,
            server_default="person",
        ),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("source_entries", postgresql.JSONB, server_default="[]"),
        sa.Column("embedding", Vector(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["kb_id"], ["knowledgebase.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_knowledge_entity_kb_type",
        "knowledge_entity",
        ["kb_id", "entity_type"],
    )

    # ---- Knowledge Graph — Relations ----
    op.create_table(
        "knowledge_relation",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kb_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("predicate", sa.String(length=200), nullable=False),
        sa.Column("object_value", sa.String(length=500), nullable=False),
        sa.Column("object_type", sa.String(length=100), nullable=False),
        sa.Column("confidence", sa.Float, server_default="0.5"),
        sa.Column("evidence_entry_ids", postgresql.JSONB, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["kb_id"], ["knowledgebase.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["subject_id"], ["knowledge_entity.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_knowledge_relation_subject",
        "knowledge_relation",
        ["subject_id"],
    )
    op.create_index(
        "ix_knowledge_relation_predicate",
        "knowledge_relation",
        ["predicate"],
    )
    op.create_index(
        "ix_knowledge_relation_kb",
        "knowledge_relation",
        ["kb_id", "predicate"],
    )


def downgrade() -> None:
    op.drop_table("knowledge_relation")
    op.drop_table("knowledge_entity")
    op.drop_index(op.f("ix_folderwatcher_folder_id"), table_name="folderwatcher")
    op.drop_index(op.f("ix_folderwatcher_is_active"), table_name="folderwatcher")
    op.drop_table("folderwatcher")
