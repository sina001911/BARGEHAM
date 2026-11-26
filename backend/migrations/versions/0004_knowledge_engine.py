"""Knowledge Engine tables: knowledgebase, knowledgeentry, knowledgedocumentlink.

Revision ID: 0004_knowledge_engine
Revises: 0003_pgvector_embedding
Create Date: 2026-11-24
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0004_knowledge_engine"
down_revision = "0003_pgvector_embedding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Knowledge bases
    op.create_table(
        "knowledgebase",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "embedding_model", sa.String(length=255), nullable=False, server_default=""
        ),
        sa.Column("embedding_dim", sa.Integer(), nullable=False, server_default="1024"),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["user.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledgebase_name"), "knowledgebase", ["name"])

    # Knowledge entries
    op.create_table(
        "knowledgeentry",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kb_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("text", sa.String(length=65535), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("section", sa.String(length=255), nullable=True),
        sa.Column(
            "direction", sa.String(length=3), nullable=False, server_default="ltr"
        ),
        sa.Column("metadata_json", sa.String(length=4096), nullable=True),
        sa.Column("tsv", postgresql.TSVECTOR(), nullable=True),
        sa.Column("embedding", Vector(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["kb_id"], ["knowledgebase.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledgeentry_kb_id"), "knowledgeentry", ["kb_id"])
    op.create_index(
        "ix_knowledgeentry_embedding",
        "knowledgeentry",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "ix_knowledgeentry_tsv",
        "knowledgeentry",
        ["tsv"],
        postgresql_using="gin",
    )

    # Document links for provenance
    op.create_table(
        "knowledgedocumentlink",
        sa.Column("entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"], ["document.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["entry_id"], ["knowledgeentry.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("entry_id", "document_id"),
    )
    op.create_index(
        op.f("ix_knowledgedocumentlink_document_id"),
        "knowledgedocumentlink",
        ["document_id"],
    )


def downgrade() -> None:
    op.drop_table("knowledgedocumentlink")
    op.drop_index("ix_knowledgeentry_tsv", table_name="knowledgeentry")
    op.drop_index("ix_knowledgeentry_embedding", table_name="knowledgeentry")
    op.drop_index(op.f("ix_knowledgeentry_kb_id"), table_name="knowledgeentry")
    op.drop_table("knowledgeentry")
    op.drop_index(op.f("ix_knowledgebase_name"), table_name="knowledgebase")
    op.drop_table("knowledgebase")
