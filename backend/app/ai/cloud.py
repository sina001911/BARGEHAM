"""OpenRouter / OpenAI-compatible cloud provider."""

from __future__ import annotations

from app.ai.providers import AIProvider, Capability, ModelInfo, ProviderType


class OpenRouterProvider(AIProvider):
    """OpenRouter cloud provider (OpenAI-compatible API)."""

    def __init__(
        self,
        base_url: str = "https://openrouter.ai/api/v1",
        api_key: str | None = None,
    ) -> None:
        super().__init__(
            provider_id="openrouter",
            provider_type=ProviderType.CLOUD,
            api_key=api_key,
        )
        self.base_url = base_url.rstrip("/")

    async def list_models(self) -> list[ModelInfo]:
        # OpenRouter model list requires an API call; return a default model
        # derived from settings so the router has something to select.
        return [
            ModelInfo(
                id="openrouter-default",
                name="OpenRouter (OpenAI-compatible)",
                provider="openrouter",
                type=ProviderType.CLOUD,
                capabilities=[Capability.CHAT],
                context_window=None,
                supports_persian=True,
            )
        ]

    async def chat(self, model_id: str, messages: list[dict], **kwargs) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )
        response = await client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=messages,
            temperature=kwargs.get("temperature", 0.1),
            max_tokens=kwargs.get("max_tokens", 2000),
        )
        return response.choices[0].message.content or ""

    async def chat_stream(self, model_id: str, messages: list[dict], **kwargs):
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )
        stream = await client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=messages,
            stream=True,
            temperature=kwargs.get("temperature", 0.1),
            max_tokens=kwargs.get("max_tokens", 2000),
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # OpenRouter does not expose a public embedding endpoint in the same way;
        # fall back to local embeddings via the registry.
        raise NotImplementedError("OpenRouter does not provide embeddings directly")

    async def health_check(self) -> bool:
        return bool(self.api_key)
