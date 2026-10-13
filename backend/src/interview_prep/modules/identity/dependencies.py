from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.db.session import get_session
from interview_prep.modules.demo.service import resolve_workspace
from interview_prep.modules.identity.models import PrincipalKind, PrincipalStatus, User
from interview_prep.modules.identity.verification import (
    AuthenticationError,
    AuthenticationUnavailable,
    TokenVerifier,
    VerifiedIdentity,
)


async def verified_identity(request: Request) -> VerifiedIdentity:
    header = request.headers.get("authorization", "")
    scheme, separator, token = header.partition(" ")
    if scheme.lower() != "bearer" or not separator or not token or " " in token:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})
    verifier: TokenVerifier = request.app.state.token_verifier
    try:
        return await verifier.verify(token)
    except AuthenticationUnavailable:
        raise HTTPException(status_code=503) from None
    except AuthenticationError:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"}) from None


async def require_account(
    identity: Annotated[VerifiedIdentity, Depends(verified_identity)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    user = await session.scalar(
        select(User).where(
            User.issuer == identity.issuer,
            User.subject == identity.subject,
            User.kind == PrincipalKind.ACCOUNT,
        )
    )
    if user is None or user.status != PrincipalStatus.ACTIVE:
        raise HTTPException(status_code=403)
    return user


async def require_demo(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    # Any Authorization header on demo routes fails; even an invalid bearer
    # token cannot downgrade an account request to a guest capability.
    if "authorization" in request.headers:
        raise HTTPException(status_code=403)
    workspace, _ = await resolve_workspace(
        session, request.cookies.get("interview_prep_demo"), datetime.now(UTC)
    )
    user = await session.get(User, workspace.id)
    if user is None:
        raise HTTPException(status_code=401)
    return user
