"""OpenRouter / OpenAI-compatible chat client — now routed through ModelRouter.

The router selects the best provider (local Ollama or cloud OpenRouter) based on
task requirements and user preference. No provider is used without explicit
configuration.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.ai.providers import registry
from app.ai.router import ModelRouter
from app.config import settings
from app.exceptions import AppException

router = ModelRouter(registry)


class LLMUnavailableError(AppException):
    def __init__(self, message: str = "AI provider is not configured") -> None:
        super().__init__(message, code="LLM_UNAVAILABLE", status_code=503)


async def _ensure_router_ready() -> None:
    """Register default providers if not yet registered."""
    if registry.list_providers():
        return

    # Register OpenRouter (cloud) if API key is configured.
    if settings.openrouter_api_key:
        from app.ai.cloud import OpenRouterProvider

        openrouter = OpenRouterProvider(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
        )
        registry.register(
            openrouter,
            default_chat=settings.prefer_cloud_chat,
            default_embedding=False,
        )

    # Register Ollama (local) — always available as an option; health-checked at runtime.
    from app.ai.local import OllamaProvider

    ollama = OllamaProvider()
    registry.register(
        ollama,
        default_chat=not settings.prefer_cloud_chat,
        default_embedding=True,
    )


def is_configured() -> bool:
    """Return True when at least one provider is registered."""
    return bool(registry.list_providers())


async def chat(
    messages: list[dict],
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
    prefer_local: bool = False,
    require_persian: bool = False,
) -> str:
    """Return a single completion for the given chat messages.

    Routes through the model router. Raises LLMUnavailableError if no provider
    is available.
    """
    await _ensure_router_ready()

    selected = await router.select_chat_model(
        prefer_local=prefer_local,
        require_persian=require_persian,
        min_context_window=None,
    )
    if selected is None:
        raise LLMUnavailableError("No chat model available")

    provider, model = selected
    try:
        return await provider.chat(
            model.id,
            messages,
            temperature=(
                settings.ai_temperature if temperature is None else temperature
            ),
            max_tokens=(
                settings.max_tokens_per_answer if max_tokens is None else max_tokens
            ),
        )
    except Exception as exc:  # noqa: BLE001
        # Fallback: try any other available chat provider.
        logger = __import__("logging").getLogger(__name__)
        logger.warning("Primary chat provider %s failed: %s", provider.provider_id, exc)

        for other_provider in registry.list_providers().values():
            if other_provider.provider_id == provider.provider_id:
                continue
            for other_model in other_provider._models.values():  # noqa: SLF001
                from app.ai.providers import Capability

                if Capability.CHAT not in other_model.capabilities:
                    continue
                try:
                    return await other_provider.chat(
                        other_model.id,
                        messages,
                        temperature=(
                            settings.ai_temperature if temperature is None else temperature
                        ),
                        max_tokens=(
                            settings.max_tokens_per_answer
                            if max_tokens is None
                            else max_tokens
                        ),
                    )
                except Exception:  # noqa: BLE001
                    continue

        raise LLMUnavailableError("All chat providers failed")


async def chat_stream(
    messages: list[dict],
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
    prefer_local: bool = False,
    require_persian: bool = False,
) -> AsyncIterator[str]:
    """Yield answer tokens as they arrive, routed through the model router."""
    await _ensure_router_ready()

    selected = await router.select_chat_model(
        prefer_local=prefer_local,
        require_persian=require_persian,
    )
    if selected is None:
        raise LLMUnavailableError("No chat model available")

    provider, model = selected
    try:
        async for token in provider.chat_stream(
            model.id,
            messages,
            temperature=(
                settings.ai_temperature if temperature is None else temperature
            ),
            max_tokens=(
                settings.max_tokens_per_answer if max_tokens is None else max_tokens
            ),
        ):
            yield token
    except Exception as exc:  # noqa: BLE001
        logger = __import__("logging").getLogger(__name__)
        logger.warning("Primary stream provider %s failed: %s", provider.provider_id, exc)

        for other_provider in registry.list_providers().values():
            if other_provider.provider_id == provider.provider_id:
                continue
            for other_model in other_provider._models.values():  # noqa: SLF001
                from app.ai.providers import Capability

                if Capability.CHAT not in other_model.capabilities:
                    continue
                try:
                    async for token in other_provider.chat_stream(
                        other_model.id,
                        messages,
                        temperature=(
                            settings.ai_temperature if temperature is None else temperature
                        ),
                        max_tokens=(
                            settings.max_tokens_per_answer
                            if max_tokens is None
                            else max_tokens
                        ),
                    ):
                        yield token
                    return
                except Exception:  # noqa: BLE001
                    continue

        raise LLMUnavailableError("All chat providers failed")
