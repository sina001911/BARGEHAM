"""Model router: intelligent task-based model selection.

Routes AI tasks (chat, embedding) to the appropriate provider and model based on
capabilities, privacy preference (local vs cloud), and task requirements.
"""

from __future__ import annotations

import logging

from app.ai.providers import AIProvider, Capability, ModelInfo, ProviderRegistry, ProviderType

logger = logging.getLogger(__name__)


class ModelRouter:
    """Selects the best provider/model for a given task."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self.registry = registry

    async def select_chat_model(
        self,
        *,
        require_vision: bool = False,
        require_tool_calling: bool = False,
        prefer_local: bool = False,
        require_persian: bool = False,
        min_context_window: int | None = None,
    ) -> tuple[AIProvider, ModelInfo] | None:
        """Select the best chat model for the given requirements.

        Returns (provider, model) or None if no suitable model exists.
        """
        candidates: list[tuple[AIProvider, ModelInfo]] = []

        for provider in self.registry.list_providers().values():
            for model in provider._models.values():  # noqa: SLF001
                if Capability.CHAT not in model.capabilities:
                    continue
                if require_vision and Capability.VISION not in model.capabilities:
                    continue
                if require_tool_calling and Capability.TOOL_CALLING not in model.capabilities:
                    continue
                if require_persian and not model.supports_persian:
                    continue
                if (
                    min_context_window is not None
                    and model.context_window is not None
                    and model.context_window < min_context_window
                ):
                    continue
                candidates.append((provider, model))

        if not candidates:
            return None

        # Prefer local providers when requested.
        if prefer_local:
            local = [(p, m) for p, m in candidates if p.provider_type == ProviderType.LOCAL]
            if local:
                candidates = local

        # Sort: local first, then larger context window, then Persian support.
        candidates.sort(
            key=lambda pm: (
                pm[0].provider_type != ProviderType.LOCAL,
                -(pm[1].context_window or 0),
                not pm[1].supports_persian,
            )
        )

        return candidates[0]

    async def select_embedding_model(self) -> tuple[AIProvider, ModelInfo] | None:
        """Select the best embedding model (prefers local)."""
        candidates: list[tuple[AIProvider, ModelInfo]] = []
        for provider in self.registry.list_providers().values():
            for model in provider._models.values():  # noqa: SLF001
                if Capability.EMBEDDING in model.capabilities:
                    candidates.append((provider, model))

        if not candidates:
            return None

        candidates.sort(
            key=lambda pm: (
                pm[0].provider_type != ProviderType.LOCAL,
                not pm[1].supports_persian,
            )
        )
        return candidates[0]

    async def health_status(self) -> dict[str, bool]:
        """Return health status per provider."""
        status: dict[str, bool] = {}
        for provider_id, provider in self.registry.list_providers().items():
            try:
                status[provider_id] = await provider.health_check()
            except Exception:  # noqa: BLE001
                status[provider_id] = False
        return status
