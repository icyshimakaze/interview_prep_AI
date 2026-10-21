CREATE FUNCTION defense_run_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.status = 'completed' OR NEW.analysis_id <> OLD.analysis_id
     OR NEW.command_key <> OLD.command_key OR NEW.question_count <> OLD.question_count
     OR NEW.revision <> OLD.revision + 1
     OR NEW.current_position NOT IN (OLD.current_position, OLD.current_position + 1)
     OR (OLD.status = 'paused' AND NEW.current_position <> OLD.current_position)
     OR (NEW.current_position > NEW.question_count AND NEW.status <> 'completed') THEN
    RAISE EXCEPTION 'Invalid defense transition' USING ERRCODE = '23514';
  END IF;
  IF NEW.current_position <> OLD.current_position AND NOT EXISTS (
    SELECT 1 FROM project_defense_answers WHERE run_id = OLD.id
      AND position = OLD.current_position AND status IN ('submitted', 'skipped')
  ) THEN
    RAISE EXCEPTION 'Unresolved defense answer' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE TRIGGER defense_run_guard BEFORE UPDATE ON project_defense_runs
FOR EACH ROW EXECUTE FUNCTION defense_run_guard();
-- statement-break
CREATE FUNCTION defense_answer_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE parent project_defense_runs;
BEGIN
  SELECT * INTO parent FROM project_defense_runs WHERE id = NEW.run_id
    AND owner_id = NEW.owner_id AND analysis_id = NEW.analysis_id FOR UPDATE;
  IF NOT FOUND OR parent.status <> 'active' OR NEW.position > parent.question_count THEN
    RAISE EXCEPTION 'Unavailable defense session' USING ERRCODE = '23514';
  END IF;
  IF TG_OP = 'INSERT' THEN
    IF NEW.status <> 'draft' OR NEW.answer_text IS NOT NULL THEN
      RAISE EXCEPTION 'Invalid initial defense answer' USING ERRCODE = '23514';
    END IF;
  ELSE
    IF OLD.status <> 'draft' OR OLD.run_id <> NEW.run_id
       OR OLD.analysis_id <> NEW.analysis_id OR OLD.question_id <> NEW.question_id
       OR OLD.position <> NEW.position OR NEW.position <> parent.current_position THEN
      RAISE EXCEPTION 'Immutable defense answer' USING ERRCODE = '23514';
    END IF;
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE TRIGGER defense_answer_guard BEFORE INSERT OR UPDATE ON project_defense_answers
FOR EACH ROW EXECUTE FUNCTION defense_answer_guard();
