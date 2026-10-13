from database_tools import disposable_database, migrate
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


async def test_resume_migration_preserves_legacy_evidence_and_refuses_lossy_rollback(
    database: AsyncEngine,
) -> None:
    async with disposable_database(database.url) as url:
        assert (await migrate(url, "upgrade", "0003_candidate_context")).returncode == 0
        engine = create_async_engine(url)
        try:
            async with engine.begin() as connection:
                owner = await connection.scalar(
                    text(
                        "INSERT INTO principals(kind,issuer,subject) "
                        "VALUES ('account','https://example.test','legacy-resume') RETURNING id"
                    )
                )
                resume = await connection.scalar(
                    text(
                        "INSERT INTO resumes(owner_id,label) "
                        "VALUES (:owner,'Original label') RETURNING id"
                    ),
                    {"owner": owner},
                )
                version = await connection.scalar(
                    text(
                        "INSERT INTO resume_versions(owner_id,resume_id,version,content_sha256,"
                        "media_type,byte_count,upload_expires_at,status) VALUES "
                        "(:owner,:resume,1,:digest,'application/pdf',100,"
                        "now()+interval '1 hour','ready') "
                        "RETURNING id"
                    ),
                    {"owner": owner, "resume": resume, "digest": "a" * 64},
                )
                await connection.execute(
                    text(
                        "INSERT INTO resume_skill_evidence(owner_id,resume_version_id,claim,"
                        "source_excerpt,source_start,source_end,review_status) VALUES "
                        "(:owner,:version,'Original claim','Original excerpt',0,16,'confirmed')"
                    ),
                    {"owner": owner, "version": version},
                )
            result = await migrate(url, "upgrade", "head")
            assert result.returncode == 0, result.stderr
            async with engine.connect() as connection:
                assert tuple(
                    (
                        await connection.execute(
                            text(
                                "SELECT claim,source_excerpt,category,origin "
                                "FROM resume_skill_evidence"
                            )
                        )
                    ).one()
                ) == ("Original claim", "Original excerpt", "other", "resume")
                assert (
                    await connection.scalar(text("SELECT content_sha256 FROM resume_versions"))
                    == "a" * 64
                )
            assert (await migrate(url, "downgrade", "0003_candidate_context")).returncode == 0
            assert (await migrate(url, "upgrade", "head")).returncode == 0
            async with engine.begin() as connection:
                await connection.execute(
                    text(
                        "INSERT INTO resume_skill_evidence"
                        "(owner_id,resume_version_id,claim,category,origin,review_status) "
                        "VALUES (:owner,:version,'Supplied claim','tool','user','confirmed')"
                    ),
                    {"owner": owner, "version": version},
                )
            refused = await migrate(url, "downgrade", "0003_candidate_context")
            assert refused.returncode != 0 and "Unsafe downgrade" in refused.stderr
            async with engine.connect() as connection:
                assert (
                    await connection.scalar(text("SELECT count(*) FROM resume_skill_evidence")) == 2
                )
                assert (
                    await connection.scalar(text("SELECT version_num FROM alembic_version"))
                    == "0004_resume_evidence"
                )
        finally:
            await engine.dispose()
