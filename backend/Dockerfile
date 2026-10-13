FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app
RUN pip install --no-cache-dir uv==0.12.24
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    UV_HTTP_TIMEOUT=120 uv sync --frozen --no-dev --no-editable
COPY alembic.ini ./
COPY alembic ./alembic

USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "interview_prep.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers", "--no-access-log"]
