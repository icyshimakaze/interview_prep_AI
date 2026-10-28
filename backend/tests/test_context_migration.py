from database_tools import disposable_database, migrate
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


async def test_context_migration_preserves_legacy_profile_and_target(database: AsyncEngine) -> None:
    async with disposable_database(database.url) as url:
        assert (await migrate(url, "upgrade", "0002_relational_model")).returncode == 0
        engine = create_async_engine(url)
        try:
            async with engine.begin() as connection:
                owner = await connection.scalar(
                    text(
                        "INSERT INTO principals(kind,issuer,subject) "
                        "VALUES ('account','https://example.test','old-owner') RETURNING id"
                    )
                )
                await connection.execute(
                    text(
                        "INSERT INTO candidate_profiles(owner_id,target_role,experience_band,"
                        "timezone,weekly_minutes,revision) "
                        "VALUES (:owner,'Original role','entry','UTC',300,5)"
                    ),
                    {"owner": owner},
                )
                target = await connection.scalar(
                    text(
                        "INSERT INTO job_targets(owner_id,title,organization) "
                        "VALUES (:owner,'Original title','Original company') RETURNING id"
                    ),
                    {"owner": owner},
                )
                await connection.execute(
                    text(
                        "INSERT INTO job_target_versions"
                        "(owner_id,target_job_id,version,description) "
                        "VALUES (:owner,:target,1,'Original supplied description')"
                    ),
                    {"owner": owner, "target": target},
                )
            upgraded = await migrate(url, "upgrade", "head")
            assert upgraded.returncode == 0, upgraded.stderr
            async with engine.connect() as connection:
                profile = (
                    await connection.execute(
                        text(
                            "SELECT target_role,weekly_minutes,revision,education,graduation_year "
                            "FROM candidate_profiles"
                        )
                    )
                ).one()
                assert tuple(profile) == ("Original role", 300, 5, None, None)
                job = (
                    await connection.execute(
                        text("SELECT title,organization,priority,status,revision FROM job_targets")
                    )
                ).one()
                assert tuple(job) == ("Original title", "Original company", "normal", "saved", 1)
                assert (
                    await connection.scalar(text("SELECT description FROM job_target_versions"))
                    == "Original supplied description"
                )
            assert (await migrate(url, "downgrade", "0002_relational_model")).returncode == 0
            assert (await migrate(url, "upgrade", "head")).returncode == 0
            async with engine.begin() as connection:
                await connection.execute(
                    text("UPDATE candidate_profiles SET education = 'Supplied education'")
                )
            refused = await migrate(url, "downgrade", "0002_relational_model")
            assert refused.returncode != 0 and "Unsafe downgrade" in refused.stderr
            async with engine.connect() as connection:
                assert (
                    await connection.scalar(text("SELECT education FROM candidate_profiles"))
                    == "Supplied education"
                )
                assert (
                    await connection.scalar(text("SELECT version_num FROM alembic_version"))
                    == "0013_better_auth"
                )
        finally:
            await engine.dispose()
