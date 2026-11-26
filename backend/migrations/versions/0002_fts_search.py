"""Add tsvector column and GIN index for full-text search.

Revision ID: 0002_fts_search
Revises: 0001_initial
Create Date: 2026-11-24
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_fts_search"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tsvector column for full-text search (nullable so existing rows stay valid).
    op.add_column(
        "textchunk",
        sa.Column("tsv", postgresql.TSVECTOR(), nullable=True),
    )
    # GIN index for fast tsvector queries.
    op.create_index(
        "ix_textchunk_tsv",
        "textchunk",
        ["tsv"],
        postgresql_using="gin",
    )
    # Backfill existing rows with a simple (language-agnostic) tsvector.
    op.execute(
        "UPDATE textchunk SET tsv = to_tsvector('simple', text) WHERE tsv IS NULL"
    )


def downgrade() -> None:
    op.drop_index("ix_textchunk_tsv", table_name="textchunk")
    op.drop_column("textchunk", "tsv")
