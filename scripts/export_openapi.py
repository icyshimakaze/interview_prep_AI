"""Export deterministic API contracts without opening a database connection."""

import argparse
import json
from pathlib import Path

from pydantic import SecretStr

from interview_prep.core.config import Settings
from interview_prep.main import create_app

TARGET = Path(__file__).resolve().parents[1] / "backend" / "openapi.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=SecretStr("postgresql+asyncpg://unused:unused@localhost/contracts_test"),
        demo_rate_limit_key=SecretStr("contract-export-only-key-not-used-by-a-running-service"),
    )
    schema = create_app(settings).openapi()
    serialized = json.dumps(schema, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not TARGET.exists() or TARGET.read_text(encoding="utf-8") != serialized:
            raise SystemExit("OpenAPI drift: run scripts/export_openapi.py and pnpm api:types")
        print("OpenAPI contracts match the application.")
    else:
        TARGET.write_text(serialized, encoding="utf-8", newline="\n")
        print("Exported backend/openapi.json.")


if __name__ == "__main__":
    main()
