"""Document comparison service.

Compares two documents (by text) and returns a structured diff of additions,
deletions, and unchanged sections, plus a similarity score.
"""

from __future__ import annotations

import difflib
import logging

from app.ai.router import ModelRouter
from app.ai.providers import registry

logger = logging.getLogger(__name__)

router = ModelRouter(registry)


def _settings_openrouter_key() -> str | None:
    from app.config import settings

    return settings.openrouter_api_key or None


async def _ensure_router_ready() -> None:
    """Register default providers if not yet registered."""
    if registry.list_providers():
        return

    from app.ai.cloud import OpenRouterProvider
    from app.ai.local import OllamaProvider

    if _settings_openrouter_key():
        openrouter = OpenRouterProvider(api_key=_settings_openrouter_key())
        registry.register(openrouter, default_chat=False)

    ollama = OllamaProvider()
    registry.register(ollama, default_chat=True, default_embedding=True)


async def compare(
    text_a: str,
    text_b: str,
    *,
    prefer_local: bool = False,
) -> dict:
    """Compare two texts and return a structured comparison result.

    Returns:
        {
            "similarity": float,          # 0..1
            "added": list[str],           # lines only in B
            "removed": list[str],         # lines only in A
            "unchanged": list[str],       # common lines
            "summary": str,               # AI-generated summary of differences
        }
    """
    if not text_a and not text_b:
        return {
            "similarity": 1.0,
            "added": [],
            "removed": [],
            "unchanged": [],
            "summary": "Both documents are empty.",
        }

    lines_a = text_a.splitlines()
    lines_b = text_b.splitlines()

    sm = difflib.SequenceMatcher(None, lines_a, lines_b, autojunk=False)
    added: list[str] = []
    removed: list[str] = []
    unchanged: list[str] = []

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            unchanged.extend(lines_a[i1:i2])
        elif tag == "delete":
            removed.extend(lines_a[i1:i2])
        elif tag == "insert":
            added.extend(lines_b[j1:j2])
        elif tag == "replace":
            removed.extend(lines_a[i1:i2])
            added.extend(lines_b[j1:j2])

    total = max(len(lines_a), len(lines_b), 1)
    similarity = len(unchanged) / total

    summary = await _ai_compare_summary(
        text_a, text_b, similarity, len(added), len(removed), prefer_local=prefer_local
    )

    return {
        "similarity": round(similarity, 4),
        "added": added[:50],
        "removed": removed[:50],
        "unchanged": unchanged[:50],
        "summary": summary,
    }


async def _ai_compare_summary(
    text_a: str,
    text_b: str,
    similarity: float,
    added_count: int,
    removed_count: int,
    *,
    prefer_local: bool,
) -> str:
    await _ensure_router_ready()

    selected = await router.select_chat_model(prefer_local=prefer_local)
    if selected is None:
        return (
            f"Documents share {similarity:.0%} of content. "
            f"Added {added_count} lines, removed {removed_count} lines."
        )

    provider, model = selected
    prompt = (
        "Compare the following two documents and summarize the key differences "
        "in Persian or English (matching the source language). Be concise.\n\n"
        f"Document A (first 3000 chars):\n{text_a[:3000]}\n\n"
        f"Document B (first 3000 chars):\n{text_b[:3000]}\n\n"
        "Summary of differences:"
    )
    try:
        return await provider.chat(
            model.id,
            [{"role": "user", "content": prompt}],
            max_tokens=300,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Comparison AI failed: %s", exc)
        return (
            f"Documents share {similarity:.0%} of content. "
            f"Added {added_count} lines, removed {removed_count} lines."
        )
