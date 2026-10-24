"""Bound request buffering before JSON decoding; never send raw exceptions to ASGI logs."""

import asyncio
import logging
from uuid import uuid4

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from interview_prep.core.errors import error_response

JSON_BYTES = 262144
READ_SECONDS = 10
logger = logging.getLogger(__name__)
UPLOADS = {
    "/api/v1/account/resumes",
    "/api/v1/demo/resume-library",
    "/api/v1/account/projects/zip",
    "/api/v1/demo/projects/zip",
}


class RequestSecurityMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.slots = asyncio.Semaphore(32)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        request.state.request_id = str(uuid4())
        started = False

        async def tracked_send(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        async def reject(status: int, code: str, message: str) -> None:
            await error_response(request, status, code, message)(scope, receive, tracked_send)

        try:
            if request.headers.get("content-encoding", "identity").lower() != "identity":
                await reject(415, "request_encoding", "Compressed request bodies are unsupported.")
                return
            # Raw uploads authenticate before their bounded streaming parser. All other
            # paths, methods and MIME types are bounded before FastAPI reads the body.
            if scope["method"] == "POST" and scope["path"] in UPLOADS:
                await self.app(scope, receive, tracked_send)
                return
            declared = request.headers.get("content-length")
            if declared is not None and (
                not declared.isascii()
                or not declared.isdigit()
                or len(declared) > 10
                or int(declared) > JSON_BYTES
            ):
                await reject(413, "request_size", "The request body exceeds 256 KiB.")
                return
            if self.slots.locked():
                await reject(503, "request_busy", "The service is busy. Try again shortly.")
                return
            async with self.slots:
                body = bytearray()
                try:
                    async with asyncio.timeout(READ_SECONDS):
                        while True:
                            message = await receive()
                            if message["type"] == "http.disconnect":
                                return
                            chunk = message.get("body", b"")
                            if len(body) + len(chunk) > JSON_BYTES:
                                await reject(
                                    413, "request_size", "The request body exceeds 256 KiB."
                                )
                                return
                            body.extend(chunk)
                            if not message.get("more_body", False):
                                break
                except TimeoutError:
                    await reject(408, "request_timeout", "The request body timed out.")
                    return
            delivered = False

            async def buffered_receive() -> Message:
                nonlocal delivered
                if delivered:
                    return await receive()
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}

            await self.app(scope, buffered_receive, tracked_send)
        except Exception:
            # Starlette's generic 500 handler re-raises to Uvicorn, which otherwise
            # logs exception messages (potentially containing candidate/provider data).
            logger.error("Unhandled request failure; request_id=%s", request.state.request_id)
            if not started:
                await reject(500, "internal_error", "An unexpected error occurred.")
