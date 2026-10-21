import hashlib
import hmac
import re
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.core.config import Settings
from interview_prep.core.security_models import EvaluationReceipt, OperationQuota
from interview_prep.modules.demo.models import DemoCreationLimit, DemoSession, DemoWorkspace
from interview_prep.modules.demo.seeding import initialize_demo
from interview_prep.modules.identity.models import PrincipalKind, PrincipalStatus, User

TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()


async def resolve_workspace(
    session: AsyncSession, token: str | None, now: datetime
) -> tuple[DemoWorkspace, DemoSession]:
    if token is None or not TOKEN_PATTERN.fullmatch(token):
        raise HTTPException(status_code=401)
    row = (
        await session.execute(
            select(DemoWorkspace, DemoSession)
            .join(DemoSession, DemoSession.workspace_id == DemoWorkspace.id)
            .join(User, User.id == DemoWorkspace.id)
            .where(
                DemoSession.token_hash == hash_token(token),
                DemoWorkspace.expires_at > now,
                User.kind == PrincipalKind.DEMO,
                User.status == PrincipalStatus.ACTIVE,
                User.expires_at > now,
            )
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=401)
    return row[0], row[1]


def verify_csrf(credential: DemoSession, csrf_token: str | None) -> None:
    if (
        csrf_token is None
        or not TOKEN_PATTERN.fullmatch(csrf_token)
        or not hmac.compare_digest(hash_token(csrf_token), credential.csrf_hash)
    ):
        raise HTTPException(status_code=403)


async def create_workspace(
    session: AsyncSession, settings: Settings, network_address: str, now: datetime
) -> tuple[DemoWorkspace, str, str]:
    window = now.replace(minute=0, second=0, microsecond=0)
    # Rotate identifiers each hour. Do not retain or log raw IP addresses.
    key = hmac.new(
        settings.demo_rate_limit_key.get_secret_value().encode(),
        f"{window.isoformat()}:{network_address}".encode(),
        hashlib.sha256,
    ).hexdigest()
    statement = insert(DemoCreationLimit).values(
        key_hash=key, window_start=window, count=1, expires_at=window + timedelta(hours=1)
    )
    limited_creation = statement.on_conflict_do_update(
        index_elements=[DemoCreationLimit.key_hash, DemoCreationLimit.window_start],
        set_={"count": DemoCreationLimit.count + 1},
        where=DemoCreationLimit.count < 2,
    ).returning(DemoCreationLimit.count)
    if await session.scalar(limited_creation) is None:
        raise HTTPException(status_code=429)

    token, csrf_token = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    principal = User(
        kind=PrincipalKind.DEMO,
        created_at=now,
        updated_at=now,
        expires_at=now + timedelta(seconds=settings.demo_ttl_seconds),
    )
    session.add(principal)
    await session.flush()
    workspace = DemoWorkspace(
        id=principal.id,
        created_at=now,
        expires_at=now + timedelta(seconds=settings.demo_ttl_seconds),
    )
    session.add(workspace)
    await session.flush()
    session.add(
        DemoSession(
            token_hash=hash_token(token),
            csrf_hash=hash_token(csrf_token),
            workspace_id=workspace.id,
        )
    )
    await initialize_demo(session, workspace.id, now)
    await session.commit()
    return workspace, token, csrf_token


async def delete_expired(session: AsyncSession, now: datetime | None = None) -> None:
    cutoff = now or datetime.now(UTC)
    await session.execute(
        delete(User).where(
            User.kind == PrincipalKind.DEMO,
            (User.expires_at <= cutoff)
            | User.id.in_(select(DemoWorkspace.id).where(DemoWorkspace.expires_at <= cutoff)),
        )
    )
    await session.execute(delete(DemoCreationLimit).where(DemoCreationLimit.expires_at <= cutoff))
    await session.execute(delete(OperationQuota).where(OperationQuota.expires_at <= cutoff))
    await session.execute(delete(EvaluationReceipt).where(EvaluationReceipt.expires_at <= cutoff))
    await session.commit()
