"""Add Audio Creation Studio tables: TTS voices, audiobooks, podcasts, scripts, versions.

Revision ID: 0010_audio_creation_studio
Revises: 0009_audio_library
Create Date: 2026-11-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers
revision = "0010_audio_creation_studio"
down_revision = "0009_audio_library"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgvector")

    # ---- TTS Voice ----
    op.create_table(
        "tts_voice",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("provider", sa.String(length=30), server_default="piper"),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("gender", sa.String(length=10), server_default="neutral"),
        sa.Column("sample_rate", sa.Integer, server_default="22050"),
        sa.Column("model_path", sa.String(length=500), nullable=True),
        sa.Column("config_path", sa.String(length=500), nullable=True),
        sa.Column("is_default_for_lang", sa.Boolean, server_default="false"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tts_voice_name"), "tts_voice", ["name"])
    op.create_index(op.f("ix_tts_voice_language"), "tts_voice", ["language"])
    op.create_index(op.f("ix_tts_voice_provider"), "tts_voice", ["provider"])

    # ---- Pronunciation Rule ----
    op.create_table(
        "pronunciation_rule",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("word", sa.String(length=200), nullable=False),
        sa.Column("replacement", sa.String(length=500), nullable=False),
        sa.Column("rule_type", sa.String(length=20), server_default="replace"),
        sa.Column("case_sensitive", sa.Boolean, server_default="false"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pronunciation_rule_language"), "pronunciation_rule", ["language"])
    op.create_index(op.f("ix_pronunciation_rule_word"), "pronunciation_rule", ["word"])

    # ---- Audiobook Project ----
    op.create_table(
        "audiobook_project",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("voice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("speed", sa.Float, server_default="1.0"),
        sa.Column("pause_between_paragraphs_ms", sa.Integer, server_default="500"),
        sa.Column("pause_between_sentences_ms", sa.Integer, server_default="200"),
        sa.Column("status", sa.String(length=20), server_default="draft"),
        sa.Column("output_path", sa.String(length=1024), nullable=True),
        sa.Column("output_format", sa.String(length=10), server_default="mp3"),
        sa.Column("total_duration_seconds", sa.Float, nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger, nullable=True),
        sa.Column("error_message", sa.String(length=2000), nullable=True),
        sa.Column("version", sa.Integer, server_default="1"),
        sa.Column("parent_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_document_id"], ["document.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["user.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["voice_id"], ["tts_voice.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["parent_version_id"], ["audiobook_project.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audiobook_project_source_document_id"),
        "audiobook_project",
        ["source_document_id"],
    )
    op.create_index(
        op.f("ix_audiobook_project_owner_id"), "audiobook_project", ["owner_id"]
    )

    # ---- Audiobook Chapter ----
    op.create_table(
        "audiobook_chapter",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("source_text", sa.Text, nullable=False),
        sa.Column("order_index", sa.Integer, server_default="0"),
        sa.Column("start_offset_seconds", sa.Float, nullable=True),
        sa.Column("end_offset_seconds", sa.Float, nullable=True),
        sa.Column("audio_path", sa.String(length=1024), nullable=True),
        sa.Column("duration_seconds", sa.Float, nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["audiobook_project.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audiobook_chapter_project_id"), "audiobook_chapter", ["project_id"]
    )

    # ---- Podcast Project ----
    op.create_table(
        "podcast_project",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("intro_music_path", sa.String(length=1024), nullable=True),
        sa.Column("outro_music_path", sa.String(length=1024), nullable=True),
        sa.Column("default_pause_ms", sa.Integer, server_default="300"),
        sa.Column("status", sa.String(length=20), server_default="draft"),
        sa.Column("output_path", sa.String(length=1024), nullable=True),
        sa.Column("output_format", sa.String(length=10), server_default="mp3"),
        sa.Column("total_duration_seconds", sa.Float, nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger, nullable=True),
        sa.Column("error_message", sa.String(length=2000), nullable=True),
        sa.Column("version", sa.Integer, server_default="1"),
        sa.Column("parent_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["user.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["parent_version_id"], ["podcast_project.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_podcast_project_owner_id"), "podcast_project", ["owner_id"]
    )

    # ---- Podcast Speaker ----
    op.create_table(
        "podcast_speaker",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("voice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=True),
        sa.Column("order_index", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["podcast_project.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["voice_id"], ["tts_voice.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_podcast_speaker_project_id"), "podcast_speaker", ["project_id"]
    )

    # ---- Podcast Segment ----
    op.create_table(
        "podcast_segment",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("speaker_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("order_index", sa.Integer, server_default="0"),
        sa.Column("voice_speed", sa.Float, nullable=True),
        sa.Column("pause_before_ms", sa.Integer, nullable=True),
        sa.Column("pause_after_ms", sa.Integer, nullable=True),
        sa.Column("emotion", sa.String(length=30), nullable=True),
        sa.Column("audio_path", sa.String(length=1024), nullable=True),
        sa.Column("duration_seconds", sa.Float, nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["podcast_project.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["speaker_id"], ["podcast_speaker.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_podcast_segment_project_id"), "podcast_segment", ["project_id"]
    )
    op.create_index(
        op.f("ix_podcast_segment_speaker_id"), "podcast_segment", ["speaker_id"]
    )

    # ---- Project Version ----
    op.create_table(
        "project_version",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_type", sa.String(length=20), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer, server_default="1"),
        sa.Column("label", sa.String(length=200), nullable=True),
        sa.Column("change_summary", sa.String(length=1000), nullable=True),
        sa.Column("snapshot_json", sa.Text, nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["user.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_version_project", "project_version", ["project_type", "project_id"]
    )


def downgrade() -> None:
    op.drop_table("project_version")
    op.drop_table("podcast_segment")
    op.drop_table("podcast_speaker")
    op.drop_table("podcast_project")
    op.drop_table("audiobook_chapter")
    op.drop_table("audiobook_project")
    op.drop_table("pronunciation_rule")
    op.drop_table("tts_voice")