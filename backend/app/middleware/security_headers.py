"""Security headers middleware."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware


def setup_security_headers(app: FastAPI) -> None:
    """Register security-related middleware."""
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],
    )