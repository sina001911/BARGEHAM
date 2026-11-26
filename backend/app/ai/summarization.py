"""Document summarization using the AI model router.

Supports extractive and abstractive summarization with configurable length.
No cloud fallback without explicit user configuration.
"""

from __future__ import annotations

import logging

from app.ai.router import ModelRouter
from app.ai.providers import registry, Capability

logger = logging.getLogger(__name__)

router = ModelRouter(registry)


async def summarize(
    text: str,
    *,
    max_length: int = 500,
    prefer_local: bool = False,
) -> str:
    """Return a summary of the given text.

    Uses the best available chat model (local preferred). Falls back to a simple
    extractive summary if no AI provider is configured.
    """
    if not text or not text.strip():
        return ""

    await _ensure_router_ready()

    selected = await router.select_chat_model(prefer_local=prefer_local)
    if selected is None:
        return _extractive_summary(text, max_length=max_length)

    provider, model = selected
    prompt = (
        "Summarize the following text concisely in Persian or English (matching the "
        "source language). Keep it under "
        f"{max_length} characters. Do not add information not present in the text.\n\n"
        f"Text:\n{text[:8000]}"
    )
    try:
        return await provider.chat(
            model.id,
            [{"role": "user", "content": prompt}],
            max_tokens=max_length // 4 + 50,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Summarization provider failed: %s", exc)
        return _extractive_summary(text, max_length=max_length)


async def _ensure_router_ready() -> None:
    """Register default providers if not yet registered."""
    if registry.list_providers():
        return

    from app.ai.cloud import OpenRouterProvider
    from app.ai.local import OllamaProvider

    if settings_openrouter_key():
        openrouter = OpenRouterProvider(api_key=settings_openrouter_key())
        registry.register(openrouter, default_chat=False)

    ollama = OllamaProvider()
    registry.register(ollama, default_chat=True, default_embedding=True)


def settings_openrouter_key() -> str | None:
    """Read OpenRouter API key from settings without importing settings at module load."""
    from app.config import settings

    return settings.openrouter_api_key or None


def _extractive_summary(text: str, *, max_length: int = 500) -> str:
    """Simple extractive summary: take the first sentences up to max_length."""
    sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
    result = ""
    for sentence in sentences:
        candidate = f"{result} {sentence}".strip()
        if len(candidate) > max_length:
            break
        result = candidate
    return result or text[:max_length]
