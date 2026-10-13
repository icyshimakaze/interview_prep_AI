"""Verify the live frontend, API and real database via public health contracts."""

import os

import httpx


def main() -> None:
    frontend = os.environ.get("FRONTEND_URL", "http://127.0.0.1:3000")
    backend = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
    with httpx.Client(timeout=15) as client:
        page = client.get(frontend)
        page.raise_for_status()
        if "Service connectivity" not in page.text:
            raise ValueError("Frontend did not render the foundation page")
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
                or payload.get("schema_revision") != "0004_resume_evidence"
            ):
                raise ValueError("Database/schema readiness failed")
    print("PASS: frontend HTTP, backend /health, PostgreSQL/schema, and same-origin connectivity.")


if __name__ == "__main__":
    main()
