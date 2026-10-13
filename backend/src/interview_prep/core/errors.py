from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException


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
    async def database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
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
        response = error_response(request, exc.status_code, code, message)
        if exc.status_code == 401 and exc.headers:
            response.headers["WWW-Authenticate"] = exc.headers.get("WWW-Authenticate", "Bearer")
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(request, 422, "validation_error", "The request is invalid.")

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return error_response(request, 500, "internal_error", "An unexpected error occurred.")
