"""Authenticate the frontend gateway before trusting its bounded quota address."""

import hmac
from ipaddress import ip_address
from uuid import uuid4

from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from interview_prep.core.config import Settings
from interview_prep.core.errors import error_response


class GatewayMiddleware:
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        self.app = app
        self.secret = settings.backend_proxy_secret.get_secret_value().encode()
        self.demo_only = settings.public_demo_only

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        path = scope["path"]
        health = path in {"/health", "/api/v1/health/ready"} and scope["method"] in {"GET", "HEAD"}
        if self.secret and not health and scope["method"] != "OPTIONS":
            supplied = request.headers.get("x-interview-prep-gateway", "").encode()
            raw_address = request.headers.get("x-interview-prep-client-ip", "")
            address: str | None = None
            if len(raw_address) <= 45:
                try:
                    address = str(ip_address(raw_address))
                except ValueError:
                    pass
            if not hmac.compare_digest(self.secret, supplied) or address is None:
                request.state.request_id = str(uuid4())
                await error_response(
                    request, 403, "gateway_required", "Use the application frontend."
                )(scope, receive, send)
                return
            scope = {**scope, "client": (address, 0)}
        if self.demo_only and path.startswith("/api/v1/account"):
            request.state.request_id = str(uuid4())
            await error_response(
                request, 403, "demo_only", "Account access is disabled on the public demo."
            )(scope, receive, send)
            return
        await self.app(scope, receive, send)
