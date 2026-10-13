"Run backend gates against a disposable PostgreSQL database, never the application DB."

import asyncio
import os
import re
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from interview_prep.core.config import get_settings

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"


async def prepare_test_database(database_url: str) -> None:
    url = make_url(database_url)
    database = url.database or ""
    application_database = make_url(get_settings().database_url.get_secret_value()).database
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,57}_test", database) or database == application_database:
        raise ValueError("Use a separate database with a safe name ending _test")
    engine = create_async_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as connection:
            exists = await connection.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": database},
            )
            if exists is not None:
                raise ValueError("Clean verification refuses an existing test database")
            await connection.execute(text(f'CREATE DATABASE "{database}"'))
    finally:
        await engine.dispose()


async def drop_created_database(database_url: str) -> None:
    url = make_url(database_url)
    database = url.database or ""
    if not re.fullmatch(r"interview_prep_[a-f0-9]{12}_test", database):
        raise ValueError("Refusing to drop an unrecognized disposable database")
    engine = create_async_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as connection:
            await connection.execute(text(f'DROP DATABASE "{database}"'))
    finally:
        await engine.dispose()


def run(arguments: list[str], environment: dict[str, str], cwd: Path = BACKEND) -> None:
    print("Running: " + " ".join(arguments), flush=True)
    subprocess.run(arguments, cwd=cwd, env=environment, check=True)


def main() -> None:
    application_url = make_url(get_settings().database_url.get_secret_value())
    template = make_url(
        os.environ.get("TEST_DATABASE_URL") or application_url.render_as_string(hide_password=False)
    )
    test_url = template.set(database=f"interview_prep_{uuid4().hex[:12]}_test").render_as_string(
        hide_password=False
    )
    asyncio.run(prepare_test_database(test_url))
    environment = {
        **os.environ,
        "DATABASE_URL": test_url,
        "TEST_DATABASE_URL": test_url,
    }
    python = sys.executable
    try:
        run([python, "-m", "ruff", "check", ".", "../scripts"], environment)
        run([python, "-m", "ruff", "format", "--check", ".", "../scripts"], environment)
        run([python, "-m", "mypy", "src", "tests", "../scripts"], environment)
        run([python, "-m", "alembic", "upgrade", "head"], environment)
        run([python, "-m", "alembic", "check"], environment)
        run([python, "-m", "pytest"], environment)
        # Round-trip only this fresh disposable DB, after tests clean their rows.
        run([python, "-m", "alembic", "downgrade", "base"], environment)
        run([python, "-m", "alembic", "upgrade", "head"], environment)
        run([python, "-m", "alembic", "check"], environment)
        run([python, "../scripts/export_openapi.py", "--check"], environment)
        run([python, "../scripts/export_legacy.py", "--check"], environment)
    finally:
        asyncio.run(drop_created_database(test_url))
    print("Backend, migrations, contracts, and legacy preservation checks passed.")


if __name__ == "__main__":
    main()
