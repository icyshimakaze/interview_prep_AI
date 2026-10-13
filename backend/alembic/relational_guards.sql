-- Frozen with revision 0002; statements are separated deliberately for asyncpg.
CREATE FUNCTION relational_touch() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.id IS DISTINCT FROM OLD.id OR NEW.created_at IS DISTINCT FROM OLD.created_at
     OR (to_jsonb(NEW)->'owner_id') IS DISTINCT FROM (to_jsonb(OLD)->'owner_id') THEN
    RAISE EXCEPTION 'Immutable identity' USING ERRCODE = '23514';
  END IF;
  NEW.updated_at := clock_timestamp();
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_question_access() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE q_owner uuid; q_visibility text; publication text;
BEGIN
  SELECT q.owner_id, q.visibility, v.status INTO q_owner, q_visibility, publication
  FROM question_versions v JOIN questions q ON q.id = v.question_id
  WHERE v.id = NEW.question_version_id FOR SHARE OF q, v;
  IF NOT FOUND OR (q_visibility = 'private' AND q_owner <> NEW.owner_id)
     OR (TG_TABLE_NAME = 'project_questions' AND q_visibility <> 'private')
     OR (TG_TABLE_NAME <> 'project_questions' AND publication <> 'published') THEN
    RAISE EXCEPTION 'Question is not available to this owner' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_question_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.status IN ('published', 'retired') AND
     (to_jsonb(NEW) - 'updated_at' - 'status') IS DISTINCT FROM
     (to_jsonb(OLD) - 'updated_at' - 'status') THEN
    RAISE EXCEPTION 'Published content is immutable' USING ERRCODE = '23514';
  END IF;
  IF OLD.status IN ('published', 'retired') AND NEW.status = 'draft' THEN
    RAISE EXCEPTION 'Published content cannot return to draft' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_curriculum_child() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE version_id uuid; publication text;
BEGIN
  version_id := CASE WHEN TG_OP = 'DELETE' THEN OLD.question_version_id ELSE NEW.question_version_id END;
  SELECT status INTO publication FROM question_versions WHERE id = version_id FOR SHARE;
  IF TG_OP = 'UPDATE' AND EXISTS (
    SELECT 1 FROM question_versions WHERE id = OLD.question_version_id
      AND status IN ('published', 'retired')
  ) THEN
    RAISE EXCEPTION 'Published rubric/options/topics are immutable' USING ERRCODE = '23514';
  END IF;
  IF publication IN ('published', 'retired') THEN
    RAISE EXCEPTION 'Published rubric/options/topics are immutable' USING ERRCODE = '23514';
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_question_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.visibility IS DISTINCT FROM OLD.visibility
     OR NEW.canonical_concept IS DISTINCT FROM OLD.canonical_concept THEN
    RAISE EXCEPTION 'Question identity is immutable' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_final_answer() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.status IN ('submitted', 'skipped') THEN
    RAISE EXCEPTION 'Final answers are immutable' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_assessment_option() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE expected uuid;
BEGIN
  SELECT question_version_id INTO expected FROM assessment_questions
    WHERE id = NEW.assessment_question_id AND owner_id = NEW.owner_id;
  IF expected IS DISTINCT FROM NEW.question_version_id THEN
    RAISE EXCEPTION 'Option version mismatch' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_selected_option() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.selected_option_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM assessment_question_options WHERE
    assessment_question_id = NEW.assessment_question_id AND owner_id = NEW.owner_id
    AND option_id = NEW.selected_option_id
  ) THEN
    RAISE EXCEPTION 'Selected option was not presented' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_project_reference() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE file_lines integer;
BEGIN
  SELECT line_count INTO file_lines FROM project_source_files
    WHERE id = NEW.source_file_id AND owner_id = NEW.owner_id AND analysis_id = NEW.analysis_id;
  IF file_lines IS NULL OR NEW.line_end > file_lines THEN
    RAISE EXCEPTION 'Invalid source citation' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_project_turn() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.project_question_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM project_questions p JOIN interview_sessions s
      ON s.owner_id = p.owner_id AND s.project_analysis_id = p.analysis_id
    WHERE s.id = NEW.session_id AND s.owner_id = NEW.owner_id
      AND p.id = NEW.project_question_id AND p.question_version_id = NEW.question_version_id
      AND EXISTS (SELECT 1 FROM project_question_citations c WHERE c.project_question_id = p.id)
  ) THEN
    RAISE EXCEPTION 'Project question context mismatch or missing citation' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_evaluation_dimension() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM answer_evaluations WHERE id =
      CASE WHEN TG_OP = 'DELETE' THEN OLD.evaluation_id ELSE NEW.evaluation_id END
      AND status IN ('completed', 'not_evaluable')
  ) THEN
    RAISE EXCEPTION 'Terminal evaluation dimensions are immutable' USING ERRCODE = '23514';
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM answer_evaluations e JOIN interview_answers a ON a.id = e.interview_answer_id
    JOIN interview_questions q ON q.id = a.interview_question_id
    JOIN question_rubric_criteria c ON c.question_version_id = q.question_version_id
    WHERE e.id = NEW.evaluation_id AND e.owner_id = NEW.owner_id AND c.id = NEW.criterion_id
      AND (NEW.answer_end IS NULL OR NEW.answer_end <= length(a.answer_text))
  ) THEN
    RAISE EXCEPTION 'Evaluation criterion or evidence mismatch' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_terminal_evaluation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.status IN ('completed', 'not_evaluable') THEN
    RAISE EXCEPTION 'Terminal evaluations require a new version' USING ERRCODE = '23514';
  END IF;
  IF NEW.supersedes_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM answer_evaluations e WHERE e.id = NEW.supersedes_id
    AND e.owner_id = NEW.owner_id AND e.interview_answer_id = NEW.interview_answer_id
    AND e.version < NEW.version
  ) THEN
    RAISE EXCEPTION 'Invalid evaluation version chain' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_progress_fact() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    RAISE EXCEPTION 'Progress facts are append-only' USING ERRCODE = '23514';
  END IF;
  IF NEW.event_type = 'assessment_completed' AND NOT EXISTS (
    SELECT 1 FROM assessment_attempts WHERE id = NEW.assessment_attempt_id
      AND owner_id = NEW.owner_id AND status = 'completed' AND completed_at = NEW.occurred_at
  ) OR NEW.event_type = 'interview_completed' AND NOT EXISTS (
    SELECT 1 FROM interview_sessions WHERE id = NEW.interview_session_id
      AND owner_id = NEW.owner_id AND status = 'completed' AND completed_at = NEW.occurred_at
  ) OR NEW.event_type = 'roadmap_item_completed' AND NOT EXISTS (
    SELECT 1 FROM roadmap_items WHERE id = NEW.roadmap_item_id
      AND owner_id = NEW.owner_id AND status = 'completed' AND completed_at = NEW.occurred_at
  ) THEN
    RAISE EXCEPTION 'Progress must reference completed work' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_demo_principal() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM principals WHERE id = NEW.id AND kind = 'demo') THEN
    RAISE EXCEPTION 'Demo workspace requires demo principal' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_publication() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.status = 'published' THEN
    IF NEW.question_type = 'short_answer' AND NOT EXISTS (
      SELECT 1 FROM short_answer_keys WHERE question_version_id = NEW.id
    ) OR NEW.question_type = 'multiple_choice' AND (
      (SELECT count(*) FROM question_options WHERE question_version_id = NEW.id) < 2
      OR NOT EXISTS (SELECT 1 FROM question_options WHERE question_version_id = NEW.id AND is_correct)
    ) OR NEW.question_type IN ('written', 'design', 'behavioral') AND (
      SELECT coalesce(sum(weight), 0) FROM question_rubric_criteria WHERE question_version_id = NEW.id
    ) <> 1 THEN
      RAISE EXCEPTION 'Published question requires a complete grading specification' USING ERRCODE = '23514';
    END IF;
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_frozen_assessment() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE parent_id uuid;
BEGIN
  parent_id := CASE WHEN TG_OP = 'DELETE' THEN OLD.assessment_id ELSE NEW.assessment_id END;
  PERFORM 1 FROM assessments WHERE id = parent_id FOR UPDATE;
  IF EXISTS (SELECT 1 FROM assessment_attempts WHERE assessment_id = parent_id)
     AND EXISTS (SELECT 1 FROM assessments WHERE id = parent_id) THEN
    RAISE EXCEPTION 'Attempted assessment allocations are frozen' USING ERRCODE = '23514';
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_attempt_parent() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  PERFORM 1 FROM assessments WHERE id = NEW.assessment_id AND owner_id = NEW.owner_id FOR UPDATE;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_principal_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.kind IS DISTINCT FROM OLD.kind OR NEW.issuer IS DISTINCT FROM OLD.issuer
     OR NEW.subject IS DISTINCT FROM OLD.subject THEN
    RAISE EXCEPTION 'Trusted identity is immutable' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_context_version() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_TABLE_NAME = 'job_target_versions' THEN
    IF (to_jsonb(NEW) - 'updated_at') IS DISTINCT FROM (to_jsonb(OLD) - 'updated_at') THEN
      RAISE EXCEPTION 'Input versions are immutable' USING ERRCODE = '23514';
    END IF;
  ELSIF TG_TABLE_NAME = 'resume_versions' THEN
    IF NEW.resume_id IS DISTINCT FROM OLD.resume_id OR NEW.version <> OLD.version
       OR NEW.content_sha256 <> OLD.content_sha256 OR NEW.byte_count <> OLD.byte_count
       OR NEW.media_type <> OLD.media_type THEN
      RAISE EXCEPTION 'Input versions are immutable' USING ERRCODE = '23514';
    END IF;
  ELSIF TG_TABLE_NAME = 'project_analyses' THEN
    IF NEW.repository_id IS DISTINCT FROM OLD.repository_id
       OR NEW.archive_sha256 <> OLD.archive_sha256
       OR NEW.commit_sha IS DISTINCT FROM OLD.commit_sha
       OR NEW.archive_bytes <> OLD.archive_bytes OR NEW.analysis_version <> OLD.analysis_version THEN
      RAISE EXCEPTION 'Input versions are immutable' USING ERRCODE = '23514';
    END IF;
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_assessment_context() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM assessment_attempts WHERE assessment_id = OLD.id) AND (
    NEW.target_job_version_id IS DISTINCT FROM OLD.target_job_version_id
    OR NEW.resume_version_id IS DISTINCT FROM OLD.resume_version_id
    OR NEW.context_version <> OLD.context_version OR NEW.policy_version <> OLD.policy_version
  ) THEN
    RAISE EXCEPTION 'Attempted assessment context is frozen' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION relational_job_source_span() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE description text;
BEGIN
  SELECT v.description INTO description FROM job_target_versions v
    WHERE v.id = NEW.target_job_version_id AND v.owner_id = NEW.owner_id;
  IF description IS NULL OR NEW.source_end > length(description)
     OR substring(description FROM NEW.source_start + 1 FOR NEW.source_end - NEW.source_start)
        <> NEW.source_excerpt THEN
    RAISE EXCEPTION 'Job evidence span does not match its source' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
