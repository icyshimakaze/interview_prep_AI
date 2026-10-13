from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from interview_prep.api.health import router as health_router
from interview_prep.core.config import Settings, get_settings
from interview_prep.core.errors import register_error_handlers
from interview_prep.db.models import Base
from interview_prep.db.session import create_engine
from interview_prep.modules.context.router import router as target_router
from interview_prep.modules.demo.router import router as demo_router
from interview_prep.modules.demo.workspace_router import router as demo_workspace_router
from interview_prep.modules.identity.router import router as account_router
from interview_prep.modules.identity.verification import TokenVerifier
from interview_prep.modules.resumes.router import router as resume_router
from interview_prep.modules.resumes.upload import PdfParser


def create_app(settings: Settings | None = None) -> FastAPI:
    configuration = settings or get_settings()
    Base.registry.configure()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(configuration)
        app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
        app.state.pdf_parser = PdfParser()
        async with httpx.AsyncClient(timeout=3, follow_redirects=False, trust_env=False) as http:
            app.state.token_verifier = TokenVerifier(configuration, http)
            try:
                yield
            finally:
                await engine.dispose()

    app = FastAPI(
        title="Interview Prep API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if configuration.app_env != "production" else None,
        redoc_url=None,
    )
    app.state.settings = configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=configuration.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "X-CSRF-Token", "Authorization", "X-Resume-Filename"],
    )

    @app.middleware("http")
    async def response_metadata(request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(demo_router)
    app.include_router(account_router)
    app.include_router(target_router)
    app.include_router(resume_router)
    app.include_router(demo_workspace_router)
    return app
