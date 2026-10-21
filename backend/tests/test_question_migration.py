from uuid import uuid4

from database_tools import disposable_database, migrate
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


async def test_question_migration_preserves_legacy_content_and_refuses_lossy_rollback(
    database: AsyncEngine,
) -> None:
    async with disposable_database(database.url) as url:
        assert (await migrate(url, "upgrade", "0004_resume_evidence")).returncode == 0
        engine = create_async_engine(url)
        question, version = uuid4(), uuid4()
        try:
            async with engine.begin() as connection:
                await connection.execute(
                    text(
                        "INSERT INTO questions(id,visibility,canonical_concept) "
                        "VALUES (:id,'global','original')"
                    ),
                    {"id": question},
                )
                await connection.execute(
                    text(
                        "INSERT INTO question_versions(id,question_id,version,title,status,"
                        "source_file,source_commit,original_topic) VALUES "
                        "(:id,:question,1,'Original title','draft','questions.json',"
                        "'48fcd90','Arrays')"
                    ),
                    {"id": version, "question": question},
                )
            upgraded = await migrate(url, "upgrade", "head")
            assert upgraded.returncode == 0, upgraded.stderr
            async with engine.connect() as connection:
                row = (
                    await connection.execute(
                        text(
                            "SELECT title,source_file,source_commit,original_topic,category "
                            "FROM question_versions"
                        )
                    )
                ).one()
                assert tuple(row) == ("Original title", "questions.json", "48fcd90", "Arrays", None)
            assert (await migrate(url, "downgrade", "0004_resume_evidence")).returncode == 0
            assert (await migrate(url, "upgrade", "head")).returncode == 0
            async with engine.begin() as connection:
                await connection.execute(
                    text("UPDATE question_versions SET category='Data Structures' WHERE id=:id"),
                    {"id": version},
                )
            refused = await migrate(url, "downgrade", "0004_resume_evidence")
            assert refused.returncode != 0 and "Unsafe downgrade" in refused.stderr
            async with engine.connect() as connection:
                assert (
                    await connection.scalar(text("SELECT title FROM question_versions"))
                    == "Original title"
                )
                assert (
                    await connection.scalar(text("SELECT version_num FROM alembic_version"))
                    == "0010_security_budgets"
                )
        finally:
            await engine.dispose()
