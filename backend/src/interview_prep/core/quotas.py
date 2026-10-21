"""Durable, atomic reservations. Failures cannot roll back consumed resource budgets."""

import hashlib
import hmac
import math
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from interview_prep.core.config import Settings
from interview_prep.core.security_models import OperationQuota


async def reserve(
    factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    owner: UUID,
    operation: Literal["ai", "import"],
    *,
    now: datetime | None = None,
) -> None:
    instant = now or datetime.now(UTC)
    hour = instant.replace(minute=0, second=0, microsecond=0)
    day = hour.replace(hour=0)
    # Import budgets cover failed files/downloads and delete/reimport loops.
    # AI budgets reserve all possible transport attempts, including retries.
    units = 1 + settings.ai_max_retries if operation == "ai" else 1
    limits = (
        [
            ("global", day, timedelta(days=1), settings.ai_global_daily_calls),
            (str(owner), day, timedelta(days=1), settings.ai_owner_daily_calls),
            (str(owner), hour, timedelta(hours=1), settings.ai_owner_hourly_calls),
        ]
        if operation == "ai"
        else [
            ("global", hour, timedelta(hours=1), 200),
            (str(owner), hour, timedelta(hours=1), 10),
        ]
    )
    async with factory() as session:
        for scope, start, duration, maximum in limits:
            digest = hmac.new(
                settings.demo_rate_limit_key.get_secret_value().encode(),
                f"{operation}:{scope}:{start.isoformat()}:{duration}".encode(),
                hashlib.sha256,
            ).hexdigest()
            statement = insert(OperationQuota).values(
                key_hash=digest, count=units, expires_at=start + duration
            )
            if (
                units > maximum
                or await session.scalar(
                    statement.on_conflict_do_update(
                        index_elements=[OperationQuota.key_hash],
                        set_={"count": OperationQuota.count + units},
                        where=OperationQuota.count + units <= maximum,
                    ).returning(OperationQuota.count)
                )
                is None
            ):
                retry_after = max(1, math.ceil((start + duration - instant).total_seconds()))
                raise HTTPException(
                    429, detail="operation_limit", headers={"Retry-After": str(retry_after)}
                )
        await session.commit()
