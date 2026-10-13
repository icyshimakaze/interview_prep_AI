from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, async_sessionmaker

from interview_prep.modules.demo.seeding import initialize_demo
from interview_prep.modules.identity.models import PrincipalKind, User


async def fictional_owner(engine: AsyncEngine) -> UUID:
    now = datetime.now(UTC)
    async with async_sessionmaker(engine)() as session, session.begin():
        user = User(kind=PrincipalKind.DEMO, expires_at=now + timedelta(hours=24))
        session.add(user)
        await session.flush()
        await initialize_demo(session, user.id, now)
        return user.id


async def reject(connection: AsyncConnection, sql: str, parameters: Mapping[str, object]) -> None:
    with pytest.raises(IntegrityError):
        async with connection.begin_nested():
            await connection.execute(text(sql), parameters)
            await connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
