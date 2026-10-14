from uuid import uuid4

from database_tools import disposable_database, migrate
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


async def test_assessment_migration_preserves_old_rows_and_refuses_new_data_loss(
    database: AsyncEngine,
) -> None:
    async with disposable_database(database.url) as url:
        assert (await migrate(url, "upgrade", "0005_question_bank")).returncode == 0
        engine = create_async_engine(url)
        owner, assessment = uuid4(), uuid4()
        try:
            async with engine.begin() as connection:
                await connection.execute(
                    text(
                        "INSERT INTO principals(id,kind,status,issuer,subject) "
                        "VALUES (:id,'account','active','migration-test','legacy')"
                    ),
                    {"id": owner},
                )
                await connection.execute(
                    text(
                        "INSERT INTO assessments(id,owner_id,title,status,"
                        "context_version,policy_version) VALUES (:id,:owner,'Previous assessment',"
                        "'ready','old-context','old-policy')"
                    ),
                    {"id": assessment, "owner": owner},
                )
            assert (await migrate(url, "upgrade", "head")).returncode == 0
            async with engine.connect() as connection:
                row = (
                    await connection.execute(
                        text(
                            "SELECT title,configuration,policy_version "
                            "FROM assessments WHERE id=:id"
                        ),
                        {"id": assessment},
                    )
                ).one()
                assert tuple(row) == ("Previous assessment", None, "old-policy")
            assert (await migrate(url, "downgrade", "0005_question_bank")).returncode == 0
            assert (await migrate(url, "upgrade", "head")).returncode == 0
            async with engine.begin() as connection:
                await connection.execute(
                    text("UPDATE assessments SET configuration='{}'::jsonb WHERE id=:id"),
                    {"id": assessment},
                )
            refused = await migrate(url, "downgrade", "0005_question_bank")
            assert refused.returncode != 0 and "Unsafe downgrade" in refused.stderr
            async with engine.connect() as connection:
                assert (
                    await connection.scalar(text("SELECT version_num FROM alembic_version"))
                    == "0006_real_assessments"
                )
                assert (
                    await connection.scalar(text("SELECT title FROM assessments"))
                    == "Previous assessment"
                )
        finally:
            await engine.dispose()
