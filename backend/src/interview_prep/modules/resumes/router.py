from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.core.errors import ErrorResponse
from interview_prep.core.quotas import reserve
from interview_prep.db.session import get_session
from interview_prep.modules.demo.workspace_router import require_demo_mutation
from interview_prep.modules.identity.dependencies import require_account, require_demo
from interview_prep.modules.identity.models import User
from interview_prep.modules.resumes import service
from interview_prep.modules.resumes.schemas import EvidenceInput, ResumeDetail, ResumeList
from interview_prep.modules.resumes.upload import PdfParser, safe_filename

Session = Annotated[AsyncSession, Depends(get_session)]
Revision = Annotated[int, Query(ge=1)]


def resume_router(mode: str) -> APIRouter:
    # Keep the historical demo /resumes/{id} summary contract unchanged.
    prefix = "resumes" if mode == "account" else "resume-library"
    router = APIRouter(
        prefix=f"/api/v1/{mode}/{prefix}",
        tags=[f"{mode}-resumes"],
        responses={
            status: {"model": ErrorResponse}
            for status in (401, 403, 404, 408, 409, 413, 415, 422, 429, 503)
        },
    )
    identity = require_account if mode == "account" else require_demo
    mutations = [Depends(require_demo_mutation)] if mode == "demo" else []

    @router.get("", response_model=ResumeList)
    async def list_resumes(
        user: Annotated[User, Depends(identity)], session: Session
    ) -> ResumeList:
        return await service.list_resumes(session, user.id)

    @router.post(
        "",
        response_model=ResumeDetail,
        status_code=201,
        dependencies=mutations,
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {
                    "application/pdf": {
                        "schema": {"type": "string", "format": "binary"},
                    }
                },
            },
        },
    )
    async def upload_resume(
        request: Request,
        user: Annotated[User, Depends(identity)],
        session: Session,
        x_resume_filename: Annotated[str, Header(max_length=1024)],
    ) -> ResumeDetail:
        label = safe_filename(x_resume_filename)
        await reserve(
            request.app.state.session_factory, request.app.state.settings, user.id, "import"
        )
        parser: PdfParser = request.app.state.pdf_parser
        data, parsed = await parser.upload(request)
        return await service.save_upload(session, user.id, label, data, parsed)

    @router.get("/{resource_id}", response_model=ResumeDetail)
    async def get_resume(
        resource_id: UUID, user: Annotated[User, Depends(identity)], session: Session
    ) -> ResumeDetail:
        return await service.get_resume(session, user.id, resource_id)

    @router.delete("/{resource_id}", status_code=204, dependencies=mutations)
    async def delete_resume(
        resource_id: UUID,
        user: Annotated[User, Depends(identity)],
        session: Session,
        expected_revision: Revision,
    ) -> Response:
        await service.delete_resume(session, user.id, resource_id, expected_revision)
        return Response(status_code=204)

    @router.post(
        "/{resource_id}/evidence",
        response_model=ResumeDetail,
        status_code=201,
        dependencies=mutations,
    )
    async def add_evidence(
        resource_id: UUID,
        body: EvidenceInput,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> ResumeDetail:
        return await service.save_evidence(session, user.id, resource_id, body)

    @router.put(
        "/{resource_id}/evidence/{evidence_id}", response_model=ResumeDetail, dependencies=mutations
    )
    async def update_evidence(
        resource_id: UUID,
        evidence_id: UUID,
        body: EvidenceInput,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> ResumeDetail:
        return await service.save_evidence(session, user.id, resource_id, body, evidence_id)

    @router.delete(
        "/{resource_id}/evidence/{evidence_id}", response_model=ResumeDetail, dependencies=mutations
    )
    async def delete_evidence(
        resource_id: UUID,
        evidence_id: UUID,
        user: Annotated[User, Depends(identity)],
        session: Session,
        expected_revision: Revision,
    ) -> ResumeDetail:
        return await service.delete_evidence(
            session, user.id, resource_id, evidence_id, expected_revision
        )

    return router


router = resume_router("account")
demo_router = resume_router("demo")
