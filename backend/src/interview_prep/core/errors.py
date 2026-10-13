from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

RESUME_ERRORS: dict[str, tuple[int, str]] = {
    "pdf_filename": (422, "Choose a .pdf filename without paths or control characters."),
    "pdf_mime": (415, "Only application/pdf uploads are accepted."),
    "pdf_size": (413, "Upload a PDF no larger than 5 MiB."),
    "pdf_corrupt": (422, "This PDF could not be read. Export a new PDF and try again."),
    "pdf_encrypted": (422, "Encrypted PDFs are unsupported. Upload an unlocked PDF."),
    "pdf_page_limit": (422, "Upload a PDF with between 1 and 20 pages."),
    "pdf_complex": (422, "This PDF exceeds safe parsing limits. Export a simpler PDF."),
    "pdf_worker_unavailable": (503, "PDF parsing is temporarily unavailable. Try again."),
    "pdf_busy": (503, "PDF parsing is busy. Please try again shortly."),
    "pdf_upload_timeout": (408, "The upload timed out. Please try again."),
    "resume_limit": (409, "You can save up to 5 resumes. Delete an unwanted resume first."),
    "evidence_limit": (409, "A resume can contain up to 100 evidence entries."),
    "resume_no_version": (409, "This resume has no parsed version. Upload a new PDF."),
    "resume_in_use": (
        409,
        "Preparation history references this resume. "
        "You can delete its evidence; deleting the resume requires removing that history.",
    ),
}


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str
    message: str
    request_id: str


def error_response(request: Request, status: int, code: str, message: str) -> JSONResponse:
    body = ErrorResponse(
        code=code, message=message, request_id=getattr(request.state, "request_id", str(uuid4()))
    )
    return JSONResponse(
        status_code=status,
        content=body.model_dump(),
        headers={
            "X-Request-ID": body.request_id,
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(SQLAlchemyError)
    @app.exception_handler(TimeoutError)
    async def database_error(request: Request, exc: SQLAlchemyError | TimeoutError) -> JSONResponse:
        return error_response(
            request, 503, "unavailable", "The service is temporarily unavailable."
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        messages = {
            401: ("unauthorized", "Valid authentication is required."),
            403: ("forbidden", "This request is not permitted."),
            404: ("not_found", "The resource was not found."),
            409: ("conflict", "The resource changed. Reload and try again."),
            422: ("validation_error", "The request is invalid."),
            429: ("rate_limited", "Demo creation limit reached. Try again in an hour."),
            503: ("unavailable", "The service is temporarily unavailable."),
        }
        code, message = messages.get(exc.status_code, ("http_error", "The request failed."))
        if exc.status_code == 409:
            conflicts = {
                "target_in_use": "This job is used by preparation history. "
                "Archive it instead of deleting it.",
                "target_limit": "You can save up to 100 target jobs. "
                "Delete an unwanted job before adding another.",
            }
            if isinstance(exc.detail, str) and exc.detail in conflicts:
                code, message = exc.detail, conflicts[exc.detail]
        response = error_response(request, exc.status_code, code, message)
        if isinstance(exc.detail, str) and exc.detail in RESUME_ERRORS:
            expected_status, safe_message = RESUME_ERRORS[exc.detail]
            if expected_status == exc.status_code:
                response = error_response(request, exc.status_code, exc.detail, safe_message)
        if exc.status_code == 401 and exc.headers:
            response.headers["WWW-Authenticate"] = exc.headers.get("WWW-Authenticate", "Bearer")
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(request, 422, "validation_error", "The request is invalid.")

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return error_response(request, 500, "internal_error", "An unexpected error occurred.")
