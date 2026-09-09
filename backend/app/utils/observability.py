"""Request-ID middleware and structured access logs."""

from __future__ import annotations

import logging
import re
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.request_context import get_request_id, set_request_id

REQUEST_ID_HEADER = "X-Request-ID"
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9_.:-]{8,128}$")
# Log a warning when a request exceeds this (basic latency visibility).
SLOW_REQUEST_MS = 1000.0

access_logger = logging.getLogger("ridecare.access")


class RequestIdLogFilter(logging.Filter):
    """Inject request_id onto every log record in the request context."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()  # type: ignore[attr-defined]
        return True


def _resolve_request_id(request: Request) -> str:
    incoming = (request.headers.get(REQUEST_ID_HEADER) or "").strip()
    if incoming and _SAFE_REQUEST_ID.match(incoming):
        return incoming
    return uuid.uuid4().hex


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach X-Request-ID and emit one structured access log per request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = _resolve_request_id(request)
        set_request_id(request_id)
        request.state.request_id = request_id

        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            duration_ms = (time.perf_counter() - started) * 1000
            access_logger.error(
                "request_id=%s method=%s path=%s status=%s duration_ms=%.1f",
                request_id,
                request.method,
                request.url.path,
                status_code,
                duration_ms,
            )
            raise
        else:
            duration_ms = (time.perf_counter() - started) * 1000
            response.headers[REQUEST_ID_HEADER] = request_id
            level = logging.WARNING if duration_ms >= SLOW_REQUEST_MS else logging.INFO
            if status_code >= 500:
                level = logging.ERROR
            elif status_code >= 400:
                level = max(level, logging.WARNING)
            access_logger.log(
                level,
                "request_id=%s method=%s path=%s status=%s duration_ms=%.1f",
                request_id,
                request.method,
                request.url.path,
                status_code,
                duration_ms,
            )
            return response
