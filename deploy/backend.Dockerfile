FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    QUESTION_CONTENT_DIR=/app/content \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app
RUN pip install --no-cache-dir uv==0.12.24
COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/src ./src
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    UV_HTTP_TIMEOUT=120 uv sync --frozen --no-dev --no-editable
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY content ./content

USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "interview_prep.serve"]
