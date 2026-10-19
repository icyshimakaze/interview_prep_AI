-- Frozen with 0007_mock_interviews. No provider call can occur inside these guards.
CREATE FUNCTION interview_session_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.contract_version <> 'interview-v1' THEN RETURN NEW; END IF;
  IF OLD.status IN ('completed','abandoned','failed') THEN
    RAISE EXCEPTION 'Closed interview is immutable' USING ERRCODE = '23514';
  END IF;
  IF OLD.status <> 'draft' AND (
    NEW.configuration IS DISTINCT FROM OLD.configuration OR
    NEW.selection_context IS DISTINCT FROM OLD.selection_context OR
    NEW.provider_descriptor IS DISTINCT FROM OLD.provider_descriptor OR
    NEW.target_job_version_id IS DISTINCT FROM OLD.target_job_version_id OR
    NEW.main_question_limit <> OLD.main_question_limit OR NEW.provider <> OLD.provider OR
    NEW.model IS DISTINCT FROM OLD.model OR NEW.contract_version <> OLD.contract_version) THEN
    RAISE EXCEPTION 'Interview context is frozen' USING ERRCODE = '23514';
  END IF;
  IF NEW.status <> OLD.status AND NOT (
    (OLD.status = 'draft' AND NEW.status IN ('active','abandoned')) OR
    (OLD.status = 'active' AND NEW.status IN ('paused','finalizing','failed')) OR
    (OLD.status = 'paused' AND NEW.status IN ('active','finalizing','failed')) OR
    (OLD.status = 'finalizing' AND NEW.status IN ('completed','abandoned','failed'))) THEN
    RAISE EXCEPTION 'Invalid interview transition' USING ERRCODE = '23514';
  END IF;
  IF NEW.status = 'completed' AND (
    NEW.end_reason <> 'full' OR
    (SELECT count(*) FROM interview_questions WHERE session_id = NEW.id
      AND parent_question_id IS NULL AND status NOT IN ('awaiting_answer','unanswered')) <> NEW.main_question_limit OR
    EXISTS (SELECT 1 FROM interview_questions WHERE session_id = NEW.id AND status = 'awaiting_answer')) THEN
    RAISE EXCEPTION 'Incomplete interview cannot complete' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION interview_turn_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE s interview_sessions; p interview_questions; f interview_followup_contents;
BEGIN
  SELECT * INTO s FROM interview_sessions WHERE id = NEW.session_id AND owner_id = NEW.owner_id FOR UPDATE;
  IF s.contract_version <> 'interview-v1' THEN
    IF NOT EXISTS (SELECT 1 FROM question_versions v JOIN questions q ON q.id = v.question_id
      WHERE v.id = NEW.question_version_id AND v.status = 'published'
      AND (q.owner_id IS NULL OR q.owner_id = NEW.owner_id)) THEN
      RAISE EXCEPTION 'Question unavailable' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF (to_jsonb(NEW) - ARRAY['updated_at','status','followup_decision','answering_ms','running_since','resolved_at'])
      IS DISTINCT FROM (to_jsonb(OLD) - ARRAY['updated_at','status','followup_decision','answering_ms','running_since','resolved_at']) THEN
      RAISE EXCEPTION 'Turn content is immutable' USING ERRCODE = '23514';
    END IF;
    IF s.status IN ('completed','abandoned','failed') THEN
      RAISE EXCEPTION 'Interview is closed' USING ERRCODE = '23514';
    END IF;
    IF NEW.status <> OLD.status AND NOT (
      (OLD.status = 'awaiting_answer' AND NEW.status IN ('submitted','skipped','unanswered')) OR
      (OLD.status = 'awaiting_answer' AND NEW.status = 'evaluated' AND OLD.parent_question_id IS NOT NULL) OR
      (OLD.status = 'submitted' AND NEW.status IN ('evaluating','evaluation_failed')) OR
      (OLD.status = 'evaluating' AND NEW.status IN ('evaluated','evaluation_failed')) OR
      (OLD.status = 'evaluation_failed' AND NEW.status = 'submitted')) THEN
      RAISE EXCEPTION 'Invalid turn transition' USING ERRCODE = '23514';
    END IF;
    IF NEW.followup_decision <> OLD.followup_decision AND NOT (
      (OLD.followup_decision = 'none' AND NEW.followup_decision = 'pending' AND OLD.parent_question_id IS NULL AND OLD.status NOT IN ('awaiting_answer','skipped','unanswered') AND s.status = 'active') OR
      (OLD.followup_decision = 'pending' AND NEW.followup_decision IN ('ready','unavailable','declined')) OR
      (OLD.followup_decision = 'ready' AND NEW.followup_decision IN ('consumed','declined'))) THEN
      RAISE EXCEPTION 'Invalid followup decision' USING ERRCODE = '23514';
    END IF;
    IF NEW.followup_decision = 'pending' AND OLD.followup_decision = 'none' AND
      (SELECT count(*) FROM interview_questions WHERE session_id = s.id AND followup_decision <> 'none') >= 3 THEN
      RAISE EXCEPTION 'Followup budget exhausted' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
  END IF;
  IF s.status <> 'active' OR NEW.status <> 'awaiting_answer' OR NEW.sequence <>
    (SELECT coalesce(max(sequence),0)+1 FROM interview_questions WHERE session_id = s.id) OR
    EXISTS (SELECT 1 FROM interview_questions WHERE session_id = s.id AND status = 'awaiting_answer') THEN
    RAISE EXCEPTION 'Invalid turn order' USING ERRCODE = '23514';
  END IF;
  IF NEW.parent_question_id IS NULL THEN
    IF NEW.source_kind <> 'bank' OR NEW.main_ordinal <>
      (SELECT count(*)+1 FROM interview_questions WHERE session_id = s.id AND parent_question_id IS NULL)
      OR NEW.main_ordinal > s.main_question_limit OR NOT EXISTS (
        SELECT 1 FROM interview_candidates c WHERE c.session_id = s.id AND c.owner_id = s.owner_id
        AND c.question_version_id = NEW.question_version_id AND c.question_id = NEW.stable_question_id) THEN
      RAISE EXCEPTION 'Invalid main allocation' USING ERRCODE = '23514';
    END IF;
  ELSE
    SELECT * INTO p FROM interview_questions WHERE id = NEW.parent_question_id AND session_id = s.id AND owner_id = s.owner_id;
    SELECT * INTO f FROM interview_followup_contents WHERE id = NEW.followup_content_id AND session_id = s.id AND owner_id = s.owner_id;
    IF p.id IS NULL OR p.parent_question_id IS NOT NULL OR p.followup_decision <> 'consumed' OR
      p.status IN ('awaiting_answer','skipped','unanswered') OR NEW.source_kind <> 'followup' OR
      f.parent_id IS DISTINCT FROM p.id OR NEW.main_ordinal IS DISTINCT FROM p.main_ordinal OR NEW.project_question_id IS NOT NULL THEN
      RAISE EXCEPTION 'Invalid followup parent' USING ERRCODE = '23514';
    END IF;
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION interview_cursor_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE s interview_sessions; latest uuid;
BEGIN
  SELECT * INTO s FROM interview_sessions WHERE id = NEW.id;
  IF NOT FOUND OR s.contract_version <> 'interview-v1' THEN RETURN NEW; END IF;
  SELECT id INTO latest FROM interview_questions WHERE session_id = s.id AND owner_id = s.owner_id ORDER BY sequence DESC LIMIT 1;
  IF s.current_turn_id IS DISTINCT FROM latest THEN
    RAISE EXCEPTION 'Invalid interview cursor' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION interview_private_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE s interview_sessions; t interview_questions;
BEGIN
  IF TG_TABLE_NAME = 'interview_candidates' THEN
    SELECT * INTO s FROM interview_sessions WHERE id = NEW.session_id AND owner_id = NEW.owner_id;
    IF TG_OP = 'UPDATE' OR NOT EXISTS (
      SELECT 1 FROM question_versions v JOIN questions q ON q.id = v.question_id
      WHERE v.id = NEW.question_version_id AND v.question_id = NEW.question_id
      AND v.status = 'published' AND (q.owner_id IS NULL OR q.owner_id = NEW.owner_id)) THEN
      RAISE EXCEPTION 'Invalid frozen candidate' USING ERRCODE = '23514';
    END IF;
  ELSIF TG_TABLE_NAME = 'interview_followup_contents' THEN
    SELECT * INTO t FROM interview_questions WHERE id = NEW.parent_id AND owner_id = NEW.owner_id;
    IF TG_OP = 'UPDATE' OR t.session_id IS DISTINCT FROM NEW.session_id OR t.parent_question_id IS NOT NULL
      OR t.followup_decision NOT IN ('pending','ready') THEN
      RAISE EXCEPTION 'Invalid private followup' USING ERRCODE = '23514';
    END IF;
  ELSIF TG_TABLE_NAME = 'interview_work' THEN
    SELECT * INTO t FROM interview_questions WHERE id = NEW.turn_id AND owner_id = NEW.owner_id;
    IF t.session_id IS DISTINCT FROM NEW.session_id OR (NEW.evaluation_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM answer_evaluations e JOIN interview_answers a ON a.id = e.interview_answer_id
      WHERE e.id = NEW.evaluation_id AND e.owner_id = NEW.owner_id AND a.interview_question_id = t.id)) THEN
      RAISE EXCEPTION 'Invalid work reference' USING ERRCODE = '23514';
    END IF;
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE FUNCTION interview_answer_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE s interview_sessions; t interview_questions;
BEGIN
  SELECT q.* INTO t FROM interview_questions q WHERE q.id = NEW.interview_question_id AND q.owner_id = NEW.owner_id;
  SELECT * INTO s FROM interview_sessions WHERE id = t.session_id AND owner_id = NEW.owner_id;
  IF s.contract_version = 'interview-v1' AND (s.status NOT IN ('active','paused') OR
    (TG_OP = 'UPDATE' AND (t.id IS DISTINCT FROM s.current_turn_id OR OLD.status <> 'draft')) OR
    length(NEW.answer_text) > 10000) THEN
    RAISE EXCEPTION 'Answer is not editable' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
