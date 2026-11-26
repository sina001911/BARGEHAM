"""Add Audio Library tables: audio files, chapters, transcription segments, playlists.

Revision ID: 0009_audio_library
Revises: 0008_folder_watcher_and_knowledge_graph
Create Date: 2026-11-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers
revision = "0009_audio_library"
down_revision = "0008_folder_watcher_and_knowledge_graph"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgvector")

    # ---- AudioFile ----
    op.create_table(
        "audiofile",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("file_name", sa.String(length=500), nullable=False),
        sa.Column("file_size", sa.Integer, server_default="0"),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("folder_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("duration_seconds", sa.Float, nullable=True),
        sa.Column("bitrate", sa.Integer, nullable=True),
        sa.Column("sample_rate", sa.Integer, nullable=True),
        sa.Column("channels", sa.Integer, nullable=True),
        sa.Column("codec", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="uploading"),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("has_transcript", sa.Boolean, server_default="false"),
        sa.Column("transcript_confidence", sa.Float, nullable=True),
        sa.Column("summary", sa.String(length=4096), nullable=True),
        sa.Column("is_deleted", sa.Boolean, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["folder_id"], ["folder.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audiofile_owner_id"), "audiofile", ["owner_id"])
    op.create_index(op.f("ix_audiofile_status"), "audiofile", ["status"])

    # ---- AudioChapter ----
    op.create_table(
        "audiochapter",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("audio_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("start_seconds", sa.Float, server_default="0"),
        sa.Column("end_seconds", sa.Float, nullable=True),
        sa.Column("order_index", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["audio_id"], ["audiofile.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audiochapter_audio_id"), "audiochapter", ["audio_id"]
    )

    # ---- TranscriptionSegment ----
    op.create_table(
        "transcriptionsegment",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("audio_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("segment_index", sa.Integer, server_default="0"),
        sa.Column("start_seconds", sa.Float, server_default="0"),
        sa.Column("end_seconds", sa.Float, server_default="0"),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("speaker", sa.String(length=50), nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("embedding", Vector(1024), nullable=True),
        sa.Column("tsv", postgresql.TSVECTOR, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["audio_id"], ["audiofile.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_transcriptionsegment_audio_id"),
        "transcriptionsegment",
        ["audio_id"],
    )
    op.create_index(
        "ix_transcriptionsegment_embedding",
        "transcriptionsegment",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "ix_transcriptionsegment_tsv",
        "transcriptionsegment",
        ["tsv"],
        postgresql_using="gin",
    )

    # ---- AudioPlaylist ----
    op.create_table(
        "audioplaylist",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audioplaylist_name"), "audioplaylist", ["name"])
    op.create_index(
        op.f("ix_audioplaylist_owner_id"), "audioplaylist", ["owner_id"]
    )

    # ---- AudioPlaylistItem ----
    op.create_table(
        "audioplaylistitem",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("playlist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("audio_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_index", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["playlist_id"], ["audioplaylist.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["audio_id"], ["audiofile.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audioplaylistitem_playlist_id"),
        "audioplaylistitem",
        ["playlist_id"],
    )


def downgrade() -> None:
    op.drop_table("audioplaylistitem")
    op.drop_table("audioplaylist")
    op.drop_table("transcriptionsegment")
    op.drop_table("audiochapter")
    op.drop_index(op.f("ix_audiofile_status"), table_name="audiofile")
    op.drop_index(op.f("ix_audiofile_owner_id"), table_name="audiofile")
    op.drop_table("audiofile")