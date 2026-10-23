import ssl
from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from interview_prep.core.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_size=3 if settings.app_env == "production" else 5,
        max_overflow=2 if settings.app_env == "production" else 10,
        connect_args={
            "timeout": settings.database_connect_timeout_seconds,
            "command_timeout": 30 if settings.app_env == "production" else 3,
            "ssl": ssl.create_default_context(cafile=settings.database_ssl_ca_file)
            if settings.database_ssl_mode == "verify-full"
            else False,
        },
        hide_parameters=True,
    )


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        session.info["settings"] = request.app.state.settings
        yield session
