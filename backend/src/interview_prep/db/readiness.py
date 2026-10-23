"""Read-only schema checks; startup never migrates or seeds persistent data."""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

SCHEMA_REVISION = "0012_ai_context_reviews"


async def verify_schema(session: AsyncSession) -> None:
    await session.execute(text("SELECT 1"))
    if await session.scalar(text("SELECT version_num FROM alembic_version")) != SCHEMA_REVISION:
        raise ValueError("Database schema mismatch")


async def require_production_database(factory: async_sessionmaker[AsyncSession]) -> None:
    try:
        async with asyncio.timeout(15), factory() as session:
            await verify_schema(session)
    except Exception:
        raise RuntimeError(
            f"Production startup requires a reachable database at migration {SCHEMA_REVISION}. "
            "Apply reviewed migrations separately; check TLS and runtime grants."
        ) from None
