"""Cross-module integration package."""
from app.integration.service import (
    audio_to_academy_lesson,
    audio_transcript_to_knowledge,
    get_workspace_stats,
    unified_search,
)

__all__ = [
    "unified_search",
    "audio_transcript_to_knowledge",
    "audio_to_academy_lesson",
    "get_workspace_stats",
]