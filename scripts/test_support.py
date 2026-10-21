"""Local test process isolation; these helpers never change persistent configuration."""

import os
import socket
import subprocess
import time

import httpx


def mock_environment() -> dict[str, str]:
    return {
        **os.environ,
        "APP_ENV": "test",
        "AUTH_ENABLED": "false",
        "AI_PROVIDER": "mock",
        "AI_TIMEOUT_SECONDS": "30",
        "AI_MAX_RETRIES": "1",
        "AI_OWNER_HOURLY_CALLS": "60",
        "AI_OWNER_DAILY_CALLS": "200",
        "AI_GLOBAL_DAILY_CALLS": "2000",
        "OPENAI_API_KEY": "",
        "OPENAI_MODEL": "",
        "OLLAMA_BASE_URL": "",
        "OLLAMA_MODEL": "",
        "CLERK_SECRET_KEY": "",
        "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY": "",
        "NEXT_TELEMETRY_DISABLED": "1",
        "DEMO_TTL_SECONDS": "86400",
        "DEMO_RATE_LIMIT_KEY": "disposable-tests-only-not-a-production-key-0001",
    }


def require_free_port(port: int) -> None:
    if not 1024 <= port <= 65535:
        raise ValueError("Test ports must be between 1024 and 65535")
    with socket.socket() as listener:
        try:
            listener.bind(("127.0.0.1", port))
        except OSError:
            raise RuntimeError(
                f"Test port {port} is unavailable (occupied or reserved); no server was stopped"
            ) from None


def stop_owned_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def wait_for_server(process: subprocess.Popen[bytes], url: str) -> None:
    deadline = time.monotonic() + 45
    with httpx.Client(timeout=2, trust_env=False) as client:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Test server exited before readiness; see .cache/browser-*.log")
            try:
                if client.get(url).is_success:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(0.25)
    raise RuntimeError("Test server did not become ready; see .cache/browser-*.log")
