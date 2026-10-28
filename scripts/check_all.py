"""Run the full supported quality pipeline sequentially against disposable data."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from test_support import mock_environment, require_free_port

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--frontend-port", type=int, default=3000)
    arguments = parser.parse_args()
    if arguments.api_port == arguments.frontend_port:
        parser.error("API and frontend must use different ports")
    for port in (arguments.api_port, arguments.frontend_port):
        require_free_port(port)
    pnpm = shutil.which("pnpm")
    if pnpm is None:
        raise SystemExit("pnpm must be installed")
    environment = mock_environment()
    # Keep the browser build and the CI production build on the same API origin.
    environment["BACKEND_INTERNAL_URL"] = f"http://127.0.0.1:{arguments.api_port}"
    os.environ.update(environment)

    def run(command: list[str]) -> None:
        print("Running: " + " ".join(command), flush=True)
        subprocess.run(command, cwd=ROOT, env=environment, check=True)

    run([sys.executable, "scripts/check_backend.py"])
    for gate in ("lint", "format:check", "typecheck", "test"):
        run([pnpm, gate])
    generated = ROOT / "frontend/src/lib/api/generated.ts"
    original = generated.read_text(encoding="utf-8")
    run([pnpm, "api:types"])
    if generated.read_text(encoding="utf-8") != original:
        raise RuntimeError(
            "Generated frontend contracts changed; review and commit them, then rerun"
        )
    run(
        [
            sys.executable,
            "scripts/check_browser.py",
            "--api-port",
            str(arguments.api_port),
            "--frontend-port",
            str(arguments.frontend_port),
        ]
    )
    print("Full backend, frontend, migration, production build and Playwright verification passed.")


if __name__ == "__main__":
    main()
