from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from relational_helpers import fictional_owner, reject
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from sqlalchemy.orm import selectinload

from interview_prep.db.models import Base
from interview_prep.modules.context.models import ProcessingStatus
from interview_prep.modules.identity.models import Profile, User
from interview_prep.modules.projects.models import (
    ProjectAnalysis,
    ProjectOrigin,
    ProjectRepository,
    SourceFile,
)


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE candidate_profiles SET weekly_minutes = 0 WHERE owner_id = :owner",
        "UPDATE job_target_versions SET description = 'changed context' WHERE owner_id = :owner",
        "UPDATE assessments SET context_version = 'changed context' WHERE owner_id = :owner",
        "UPDATE evaluation_dimensions SET score = 1 WHERE owner_id = :owner",
        "UPDATE assessment_attempts SET status = 'fabricated' WHERE owner_id = :owner",
        (
            "UPDATE question_attempts SET answer_text = 'changed final answer'"
            " WHERE owner_id = :owner"
        ),
        (
            "UPDATE interview_answers SET answer_text = 'changed final answer'"
            " WHERE owner_id = :owner"
        ),
        (
            "UPDATE question_versions SET prompt = 'changed published prompt' "
            "WHERE id IN (SELECT v.id FROM question_versions v JOIN questions "
            "q ON q.id=v.question_id WHERE q.owner_id=:owner)"
        ),
        (
            "UPDATE short_answer_keys SET normalized_answer = 'changed key' WH"
            "ERE question_version_id IN (SELECT v.id FROM question_versions v "
            "JOIN questions q ON q.id=v.question_id WHERE q.owner_id=:owner)"
        ),
        (
            "UPDATE answer_evaluations SET feedback = 'mutated historical resu"
            "lt' WHERE owner_id = :owner"
        ),
        "UPDATE progress_events SET result_kind = 'deterministic' WHERE owner_id = :owner",
        (
            "INSERT INTO candidate_profiles (owner_id,target_role,experience_b"
            "and,timezone,weekly_minutes) VALUES (:owner,'x','entry','UTC',240"
            ")"
        ),
        (
            "INSERT INTO question_attempts (owner_id,assessment_id,assessment_"
            "attempt_id,assessment_question_id,status,answer_text,submitted_at"
            ",submission_key) SELECT owner_id,assessment_id,assessment_attempt"
            "_id,assessment_question_id,status,answer_text,submitted_at,gen_ra"
            "ndom_uuid() FROM question_attempts WHERE owner_id=:owner LIMIT 1"
        ),
        (
            "INSERT INTO assessment_questions (owner_id,assessment_id,question"
            "_version_id,position) SELECT owner_id,assessment_id,question_vers"
            "ion_id,12 FROM assessment_questions WHERE owner_id=:owner LIMIT 1"
        ),
    ],
)
async def test_database_constraints_and_immutable_history(database: AsyncEngine, sql: str) -> None:
    owner = await fictional_owner(database)
    async with database.begin() as connection:
        await reject(connection, sql, {"owner": owner})


@pytest.mark.parametrize(
    "sql",
    [
        (
            "INSERT INTO resume_versions (owner_id,resume_id,version,content_s"
            "ha256,media_type,byte_count,upload_expires_at,status) SELECT :for"
            "eign,resume_id,2,content_sha256,media_type,byte_count,upload_expi"
            "res_at,status FROM resume_versions WHERE owner_id=:owner LIMIT 1"
        ),
        (
            "INSERT INTO bookmarks (owner_id,question_version_id) SELECT :fore"
            "ign,v.id FROM question_versions v JOIN questions q ON q.id=v.ques"
            "tion_id WHERE q.owner_id=:owner LIMIT 1"
        ),
        (
            "INSERT INTO roadmap_items (owner_id,roadmap_id,title,position,est"
            "imated_minutes,status) SELECT :foreign,roadmap_id,'foreign task',"
            "20,30,'planned' FROM roadmap_items WHERE owner_id=:owner LIMIT 1"
        ),
        (
            "INSERT INTO resume_skill_evidence (owner_id,resume_version_id,cla"
            "im,source_excerpt,source_start,source_end,review_status) SELECT :"
            "foreign,id,'x','x',0,1,'confirmed' FROM resume_versions WHERE own"
            "er_id=:owner LIMIT 1"
        ),
        (
            "INSERT INTO job_skill_requirements (owner_id,target_job_version_i"
            "d,source_excerpt,source_start,source_end,priority,review_status) "
            "SELECT :foreign,id,'x',0,1,'essential','confirmed' FROM job_targe"
            "t_versions WHERE owner_id=:owner LIMIT 1"
        ),
    ],
)
async def test_compound_ownership_and_private_curriculum(database: AsyncEngine, sql: str) -> None:
    owner = await fictional_owner(database)
    foreign = await fictional_owner(database)
    async with database.begin() as connection:
        await reject(connection, sql, {"owner": owner, "foreign": foreign})


async def test_delete_owner_cascades_private_graph_and_preserves_other_owner(
    database: AsyncEngine,
) -> None:
    first = await fictional_owner(database)
    second = await fictional_owner(database)
    async with async_sessionmaker(database)() as session:
        await session.execute(delete(User).where(User.id == first))
        await session.commit()
        assert await session.get(User, first) is None
        assert await session.scalar(select(Profile).where(Profile.owner_id == second)) is not None
        for table in Base.metadata.tables.values():
            if "owner_id" in table.c:
                assert (
                    await session.scalar(
                        select(func.count()).select_from(table).where(table.c.owner_id == first)
                    )
                    == 0
                )


async def test_project_relationships_paths_ownership_and_line_citations(
    database: AsyncEngine,
) -> None:
    owner = await fictional_owner(database)
    foreign = await fictional_owner(database)
    async with async_sessionmaker(database)() as session, session.begin():
        repository = ProjectRepository(
            owner_id=owner, name="Synthetic test project", origin=ProjectOrigin.ZIP
        )
        session.add(repository)
        await session.flush()
        analysis = ProjectAnalysis(
            owner_id=owner,
            repository_id=repository.id,
            archive_sha256="1" * 64,
            archive_bytes=100,
            upload_expires_at=datetime.now(UTC) + timedelta(hours=24),
            analysis_version="test-v1",
            status=ProcessingStatus.READY,
        )
        session.add(analysis)
        await session.flush()
        source = SourceFile(
            owner_id=owner,
            analysis_id=analysis.id,
            path="src/example.py",
            content_sha256="2" * 64,
            byte_count=10,
            line_count=2,
            retained_text="print(1)\n",
        )
        session.add(source)
        await session.flush()
        analysis_id, file_id = analysis.id, source.id
    async with async_sessionmaker(database)() as session:
        result = await session.scalar(
            select(ProjectAnalysis)
            .options(selectinload(ProjectAnalysis.files))
            .where(ProjectAnalysis.id == analysis_id, ProjectAnalysis.owner_id == owner)
        )
        assert result is not None and result.files[0].path == "src/example.py"
    async with database.begin() as connection:
        values = {"owner": owner, "foreign": foreign, "analysis": analysis_id, "file": file_id}
        await reject(
            connection,
            (
                "INSERT INTO project_facts (owner_id,analysis_id,source_file_id,fa"
                "ct_type,description,line_start,line_end) VALUES (:owner,:analysis"
                ",:file,'route','out of bounds',1,3)"
            ),
            values,
        )
        await reject(
            connection,
            (
                "INSERT INTO project_facts (owner_id,analysis_id,source_file_id,fa"
                "ct_type,description,line_start,line_end) VALUES (:foreign,:analys"
                "is,:file,'route','foreign source',1,2)"
            ),
            values,
        )
        await reject(
            connection,
            (
                "INSERT INTO project_source_files (owner_id,analysis_id,path,conte"
                "nt_sha256,byte_count,line_count) VALUES (:owner,:analysis,'../sec"
                "ret','00000000000000000000000000000000000000000000000000000000000"
                "00000',1,1)"
            ),
            values,
        )


async def test_question_attempt_cannot_mix_assessments(database: AsyncEngine) -> None:
    owner = await fictional_owner(database)
    async with database.begin() as connection:
        other = uuid4()
        await connection.execute(
            text(
                "INSERT INTO assessments (id,owner_id,title,status,context_version"
                ",policy_version) VALUES (:id,:owner,'Other','draft','v1','v1')"
            ),
            {"id": other, "owner": owner},
        )
        await reject(
            connection,
            (
                "INSERT INTO question_attempts (owner_id,assessment_id,assessment_"
                "attempt_id,assessment_question_id,status) SELECT owner_id,:other,"
                "id,(SELECT id FROM assessment_questions WHERE owner_id=:owner LIM"
                "IT 1),'draft' FROM assessment_attempts WHERE owner_id=:owner LIMI"
                "T 1"
            ),
            {"owner": owner, "other": other},
        )


async def test_score_and_json_metadata_constraints(database: AsyncEngine) -> None:
    owner = await fictional_owner(database)
    async with database.begin() as connection:
        answer_id = await connection.scalar(
            text("SELECT id FROM interview_answers WHERE owner_id=:owner"), {"owner": owner}
        )
        for score, metadata in [
            (101, "{}"),
            (-1, "{}"),
            (50, "[]"),
            (50, '{"large":"' + "x" * 9000 + '"}'),
        ]:
            await reject(
                connection,
                "INSERT INTO answer_evaluations (owner_id,interview_answer_id,version,kind,"
                "status,evaluator_version,rubric_version,score,usage_metadata) "
                "VALUES (:owner,:answer,2,'simulation','completed','v1','v1',"
                ":score,CAST(:metadata AS jsonb))",
                {"owner": owner, "answer": answer_id, "score": score, "metadata": metadata},
            )


async def test_draft_global_questions_cannot_be_used_or_published_incomplete(
    database: AsyncEngine,
) -> None:
    from test_seeding import MANIFEST

    from interview_prep.seeding import load_legacy_seed

    owner = await fictional_owner(database)
    async with async_sessionmaker(database)() as session, session.begin():
        await load_legacy_seed(session, MANIFEST)
    async with database.begin() as connection:
        version_id = await connection.scalar(
            text(
                "SELECT v.id FROM question_versions v JOIN questions q ON q.id=v.question_id "
                "WHERE q.owner_id IS NULL LIMIT 1"
            )
        )
        await reject(
            connection,
            "INSERT INTO bookmarks (owner_id,question_version_id) VALUES (:owner,:version)",
            {"owner": owner, "version": version_id},
        )
        await reject(
            connection,
            "UPDATE question_versions SET status='published' WHERE id=:version",
            {"version": version_id},
        )
