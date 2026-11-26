"""Redis-based rate limiting middleware."""
from __future__ import annotations

import time

import redis.asyncio as redis
from fastapi import HTTPException, Request, status

from app.config import settings


def _client() -> redis.Redis | None:
    try:
        return redis.from_url(settings.redis_url, decode_responses=True)
    except Exception:
        return None


class RateLimitMiddleware:
    """Sliding-window rate limiter keyed by path + client IP."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        path = request.url.path

        limits: dict[str, int] = {
            "/auth/login": settings.rate_limit_auth,
            "/auth/register": settings.rate_limit_auth,
            "/auth/refresh": settings.rate_limit_auth,
            "/search": settings.rate_limit_search,
        }
        limit = next((v for prefix, v in limits.items() if path.startswith(prefix)), 0)
        if limit <= 0:
            await self.app(scope, receive, send)
            return

        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}:{path}"
        window = 60

        client = _client()
        if client is None:
            await self.app(scope, receive, send)
            return

        try:
            now = time.time()
            await client.zremrangebyscore(key, 0, now - window)
            count = await client.zcard(key)
            if count >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                )
            await client.zadd(key, {str(now): now})
            await client.expire(key, window)
        except HTTPException:
            raise
        except Exception:
            pass

        await self.app(scope, receive, send)