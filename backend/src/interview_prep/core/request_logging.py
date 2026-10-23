"""Content-free request metadata. Never log raw URL paths, queries or identities."""

import json
import logging

from fastapi import Request

logger = logging.getLogger("interview_prep.requests")
METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


def configure_request_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False


def record_request(request: Request, status: int, elapsed_seconds: float) -> None:
    route = getattr(request.scope.get("route"), "path", "unmatched")
    logger.info(
        "%s",
        json.dumps(
            {
                "event": "http_request",
                "method": request.method if request.method in METHODS else "OTHER",
                "route": route,
                "status": status,
                "duration_ms": round(elapsed_seconds * 1000),
                "request_id": request.state.request_id,
            }
        ),
    )
