"""Resolve authenticated provider bindings without changing business owner UUIDs."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.identity.models import PrincipalIdentity, PrincipalKind, User
from interview_prep.modules.identity.verification import VerifiedIdentity


async def find_account(
    session: AsyncSession, identity: VerifiedIdentity, *, bindings: bool
) -> User | None:
    query = select(User).where(User.kind == PrincipalKind.ACCOUNT)
    if bindings:
        query = query.join(PrincipalIdentity, PrincipalIdentity.principal_id == User.id).where(
            PrincipalIdentity.issuer == identity.issuer,
            PrincipalIdentity.subject == identity.subject,
        )
    else:
        query = query.where(User.issuer == identity.issuer, User.subject == identity.subject)
    return await session.scalar(query)


async def bootstrap_account(
    session: AsyncSession, identity: VerifiedIdentity, *, bindings: bool
) -> User | None:
    existing = await find_account(session, identity, bindings=bindings)
    if existing is not None:
        return existing
    await session.execute(
        insert(User)
        .values(kind=PrincipalKind.ACCOUNT, issuer=identity.issuer, subject=identity.subject)
        .on_conflict_do_nothing(index_elements=[User.issuer, User.subject])
    )
    user = await find_account(session, identity, bindings=False)
    if bindings and user is not None:
        await session.execute(
            insert(PrincipalIdentity)
            .values(principal_id=user.id, issuer=identity.issuer, subject=identity.subject)
            .on_conflict_do_nothing(
                index_elements=[PrincipalIdentity.issuer, PrincipalIdentity.subject]
            )
        )
        return await find_account(session, identity, bindings=True)
    return user
