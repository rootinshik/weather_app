"""Request logging middleware — writes each API request to request_logs table."""

import asyncio
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.database import AsyncSessionLocal
from app.models.request_log import RequestLog

logger = logging.getLogger(__name__)

# Paths that should not be logged (health checks, docs, static assets)
_SKIP_PATHS = frozenset({
    "/health",
    "/readiness",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/docs/oauth2-redirect",
})


async def _write_log(platform: str, action: str, request_meta: dict) -> None:
    """Write a single request log entry (fire-and-forget)."""
    try:
        async with AsyncSessionLocal() as db:
            db.add(RequestLog(platform=platform, action=action, request_meta=request_meta))
            await db.commit()
    except Exception as exc:
        logger.debug("Request logging failed (non-critical): %s", exc)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that asynchronously logs every API request to request_logs."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        path = request.url.path
        if path in _SKIP_PATHS:
            return response

        asyncio.create_task(
            _write_log(
                platform="web",
                action=f"{request.method} {path}",
                request_meta={"status_code": response.status_code},
            )
        )

        return response
