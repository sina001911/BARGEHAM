"""Local AI providers (Ollama, etc.).

These providers run entirely on the user's device. No data leaves the machine
unless the user explicitly configures a cloud provider.
"""

from __future__ import annotations

import json
import logging

import httpx

from app.ai.providers import AIProvider, Capability, ModelInfo, ProviderType

logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    """Ollama local LLM provider (http://localhost:11434)."""

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        super().__init__(
            provider_id="ollama",
            provider_type=ProviderType.LOCAL,
            api_key=None,
        )
        self.base_url = base_url.rstrip("/")

    async def list_models(self) -> list[ModelInfo]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.warning("Ollama discovery failed: %s", exc)
            return []

        models: list[ModelInfo] = []
        for item in data.get("models", []):
            model_id = item.get("name", "")
            models.append(
                ModelInfo(
                    id=model_id,
                    name=model_id,
                    provider="ollama",
                    type=ProviderType.LOCAL,
                    capabilities=[Capability.CHAT, Capability.EMBEDDING],
                    context_window=None,
                    supports_persian=True,
                )
            )
        return models

    async def chat(self, model_id: str, messages: list[dict], **kwargs) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/chat",
                json={"model": model_id, "messages": messages, "stream": False, **kwargs},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")

    async def chat_stream(
        self, model_id: str, messages: list[dict], **kwargs
    ):
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={"model": model_id, "messages": messages, "stream": True, **kwargs},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            payload = json.loads(line[6:])
                        except json.JSONDecodeError:
                            continue
                        if "message" in payload and "content" in payload["message"]:
                            yield payload["message"]["content"]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                resp = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": "default", "prompt": text},
                )
                resp.raise_for_status()
                data = resp.json()
                vectors.append(data.get("embedding", []))
        return vectors

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False
