"""Container entry point for platforms assigning the HTTP listener through PORT."""

import os

import uvicorn

from interview_prep.core.request_logging import configure_request_logging


def listen_port(value: str | None) -> int:
    raw = value if value is not None else "8000"
    if not raw.isascii() or not raw.isdigit() or not 1 <= int(raw) <= 65535:
        raise ValueError("PORT must be an integer between 1 and 65535")
    return int(raw)


def main() -> None:
    configure_request_logging()
    uvicorn.run(
        "interview_prep.main:create_app",
        factory=True,
        host="0.0.0.0",
        port=listen_port(os.environ.get("PORT")),
        proxy_headers=False,
        access_log=False,
    )


if __name__ == "__main__":
    main()
