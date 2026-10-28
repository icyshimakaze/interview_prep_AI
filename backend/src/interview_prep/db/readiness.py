"""Read-only schema checks; startup never migrates or seeds persistent data."""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

SCHEMA_REVISION = "0013_better_auth"
COMPATIBLE_REVISIONS = {"0012_ai_context_reviews", SCHEMA_REVISION}


async def verify_schema(session: AsyncSession, *, require_auth: bool = False) -> str:
    await session.execute(text("SELECT 1"))
    revision = await session.scalar(text("SELECT version_num FROM alembic_version"))
    if revision not in ({SCHEMA_REVISION} if require_auth else COMPATIBLE_REVISIONS):
        raise ValueError("Database schema mismatch")
    return str(revision)


async def require_production_database(
    factory: async_sessionmaker[AsyncSession], *, require_auth: bool = False
) -> None:
    try:
        async with asyncio.timeout(15), factory() as session:
            await verify_schema(session, require_auth=require_auth)
    except Exception:
        raise RuntimeError(
            f"Production startup requires a reachable database at migration {SCHEMA_REVISION}. "
            "Apply reviewed migrations separately; check TLS and runtime grants."
        ) from None
