import asyncio
import os
import subprocess
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine

BACKEND = Path(__file__).resolve().parents[1]


@asynccontextmanager
async def disposable_database(source: URL) -> AsyncIterator[str]:
    name = f"interview_prep_{uuid4().hex[:12]}_test"
    admin = create_async_engine(source.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        async with admin.connect() as connection:
            await connection.execute(text(f'CREATE DATABASE "{name}"'))
        try:
            yield source.set(database=name).render_as_string(hide_password=False)
        finally:
            async with admin.connect() as connection:
                await connection.execute(text(f'DROP DATABASE "{name}"'))
    finally:
        await admin.dispose()


async def migrate(url: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-m", "alembic", *arguments],
        cwd=BACKEND,
        env={**os.environ, "DATABASE_URL": url},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
