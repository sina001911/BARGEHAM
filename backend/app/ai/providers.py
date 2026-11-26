"""AI provider abstraction and registry.

Supports multiple backends:
- OpenRouter / OpenAI-compatible (cloud)
- Ollama (local)
- llama.cpp / LM Studio (local OpenAI-compatible)
- Sentence-transformers (local embeddings)

No provider is silently used without explicit user configuration.
"""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    CLOUD = "cloud"
    LOCAL = "local"


class Capability(str, Enum):
    CHAT = "chat"
    EMBEDDING = "embedding"
    VISION = "vision"
    AUDIO = "audio"
    TOOL_CALLING = "tool_calling"


@dataclass
class ModelInfo:
    id: str
    name: str
    provider: str
    type: ProviderType
    capabilities: list[Capability] = field(default_factory=list)
    context_window: int | None = None
    supports_persian: bool = False


class AIProvider(abc.ABC):
    """Abstract base for AI providers."""

    def __init__(
        self,
        provider_id: str,
        provider_type: ProviderType,
        api_key: str | None = None,
    ) -> None:
        self.provider_id = provider_id
        self.provider_type = provider_type
        self.api_key = api_key
        self._models: dict[str, ModelInfo] = {}

    @abc.abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """Discover available models from this provider."""

    @abc.abstractmethod
    async def chat(self, model_id: str, messages: list[dict], **kwargs: Any) -> str:
        """Return a single completion for the given chat messages."""

    @abc.abstractmethod
    async def chat_stream(
        self, model_id: str, messages: list[dict], **kwargs: Any
    ):
        """Yield answer tokens as they arrive."""

    @abc.abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts."""

    @abc.abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is reachable."""

    def get_model(self, model_id: str) -> ModelInfo | None:
        return self._models.get(model_id)

    def register_model(self, model: ModelInfo) -> None:
        self._models[model.id] = model


class ProviderRegistry:
    """Registry of AI providers."""

    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}
        self._default_chat_provider: str | None = None
        self._default_embedding_provider: str | None = None

    def register(
        self,
        provider: AIProvider,
        *,
        default_chat: bool = False,
        default_embedding: bool = False,
    ) -> None:
        self._providers[provider.provider_id] = provider
        if default_chat:
            self._default_chat_provider = provider.provider_id
        if default_embedding:
            self._default_embedding_provider = provider.provider_id

    def get(self, provider_id: str) -> AIProvider | None:
        return self._providers.get(provider_id)

    def list_providers(self) -> dict[str, AIProvider]:
        return dict(self._providers)

    @property
    def default_chat_provider(self) -> AIProvider | None:
        if self._default_chat_provider:
            return self._providers.get(self._default_chat_provider)
        return None

    @property
    def default_embedding_provider(self) -> AIProvider | None:
        if self._default_embedding_provider:
            return self._providers.get(self._default_embedding_provider)
        return None


# Global registry instance (populated at startup)
registry = ProviderRegistry()
