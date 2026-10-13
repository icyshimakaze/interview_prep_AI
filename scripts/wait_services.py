"""Bounded startup polling for CI and local development."""

import os
import time

import httpx


def main() -> None:
    urls = [
        os.environ.get("FRONTEND_URL", "http://127.0.0.1:3000"),
        os.environ.get("BACKEND_URL", "http://127.0.0.1:8000") + "/api/v1/health/ready",
    ]
    deadline = time.monotonic() + 60
    with httpx.Client(timeout=3) as client:
        while time.monotonic() < deadline:
            try:
                if all(client.get(url).is_success for url in urls):
                    print("Frontend and backend are ready.")
                    return
            except httpx.HTTPError:
                pass
            time.sleep(1)
    raise SystemExit("Services did not become ready within 60 seconds")


if __name__ == "__main__":
    main()
