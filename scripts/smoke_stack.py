"""Verify the live frontend, API and real database via public health contracts."""

import os

import httpx

from interview_prep.api.health import SCHEMA_REVISION


def main() -> None:
    frontend = os.environ.get("FRONTEND_URL", "http://127.0.0.1:3000")
    backend = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
    with httpx.Client(timeout=15, trust_env=False) as client:
        page = client.get(frontend)
        page.raise_for_status()
        if "<h1" not in page.text or 'href="/demo"' not in page.text:
            raise ValueError("Frontend did not render the landing page and demo entry")
        health = client.get(f"{backend}/health")
        health.raise_for_status()
        if health.json() != {"status": "ok", "service": "interview-prep-api"}:
            raise ValueError("Unexpected liveness contract")
        for origin in (backend, frontend):
            readiness = client.get(f"{origin}/api/v1/health/ready")
            readiness.raise_for_status()
            payload = readiness.json()
            if (
                payload.get("database") != "connected"
                or payload.get("schema_revision") != SCHEMA_REVISION
            ):
                raise ValueError("Database/schema readiness failed")
    print("PASS: frontend HTTP, backend /health, PostgreSQL/schema, and same-origin connectivity.")


if __name__ == "__main__":
    main()
