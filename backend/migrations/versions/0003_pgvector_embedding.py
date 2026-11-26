"""Convert embedding column from JSONB to pgvector vector(1024).

Revision ID: 0003_pgvector_embedding
Revises: 0002_fts_search
Create Date: 2026-11-24
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_pgvector_embedding"
down_revision = "0002_fts_search"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL cannot cast jsonb directly to vector. Drop and recreate the
    # column as vector(1024), then rebuild the HNSW index.
    op.drop_column("textchunk", "embedding")
    op.execute("ALTER TABLE textchunk ADD COLUMN embedding vector(1024)")
    op.execute(
        "CREATE INDEX ix_textchunk_embedding ON textchunk "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_index("ix_textchunk_embedding", table_name="textchunk")
    op.drop_column("textchunk", "embedding")
    op.execute("ALTER TABLE textchunk ADD COLUMN embedding JSONB")
