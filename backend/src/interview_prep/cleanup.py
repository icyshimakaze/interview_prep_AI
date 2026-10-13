import argparse
import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker

from interview_prep.core.config import get_settings
from interview_prep.db.session import create_engine
from interview_prep.modules.demo.service import delete_expired


async def cleanup(repeat: bool = False) -> None:
    engine = create_engine(get_settings())
    try:
        while True:
            async with async_sessionmaker(engine)() as session:
                await delete_expired(session)
            if not repeat:
                break
            await asyncio.sleep(3600)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Delete expired demo rows; never accept personal data."
    )
    parser.add_argument("--repeat", action="store_true", help="Run hourly until stopped")
    asyncio.run(cleanup(repeat=parser.parse_args().repeat))
