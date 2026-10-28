from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.db.session import get_session
from interview_prep.modules.demo.service import resolve_workspace
from interview_prep.modules.identity.accounts import find_account
from interview_prep.modules.identity.models import PrincipalStatus, User
from interview_prep.modules.identity.verification import (
    AuthenticationError,
    AuthenticationUnavailable,
    TokenVerifier,
    VerifiedIdentity,
)


async def verified_identity(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> VerifiedIdentity:
    header = request.headers.get("authorization", "")
    scheme, separator, token = header.partition(" ")
    if scheme.lower() != "bearer" or not separator or not token or " " in token:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})
    verifier: TokenVerifier = request.app.state.token_verifier
    try:
        identity = await verifier.verify(token)
        if verifier.settings.auth_provider == "better_auth":
            active = await session.scalar(
                text(
                    "SELECT EXISTS (SELECT 1 FROM auth.api_sessions WHERE id=:sid "
                    "AND user_id=:subject AND expires_at > CURRENT_TIMESTAMP)"
                ),
                {"sid": identity.session_id, "subject": identity.subject},
            )
            if not active:
                raise AuthenticationError()
        return identity
    except (AuthenticationUnavailable, SQLAlchemyError):
        raise HTTPException(status_code=503) from None
    except AuthenticationError:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"}) from None


async def require_account(
    request: Request,
    identity: Annotated[VerifiedIdentity, Depends(verified_identity)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    user = await find_account(
        session, identity, bindings=request.app.state.settings.auth_provider == "better_auth"
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
