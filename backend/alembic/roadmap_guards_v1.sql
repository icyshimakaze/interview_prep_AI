CREATE FUNCTION personal_roadmap_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.generation_key IS NOT NULL AND (
    (to_jsonb(NEW) - ARRAY['status','revision','updated_at']) IS DISTINCT FROM
    (to_jsonb(OLD) - ARRAY['status','revision','updated_at'])
    OR NEW.revision <> OLD.revision + 1
    OR NEW.status NOT IN ('active','archived')
    OR (OLD.status = 'archived' AND NEW.status <> 'archived')
  ) THEN
    RAISE EXCEPTION 'Immutable roadmap generation or invalid revision' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE TRIGGER personal_roadmap_guard BEFORE UPDATE ON roadmaps
FOR EACH ROW EXECUTE FUNCTION personal_roadmap_guard();
-- statement-break
CREATE FUNCTION personal_roadmap_item_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.recommendation IS NOT NULL AND (
    (to_jsonb(NEW) - ARRAY['status','completed_at','updated_at']) IS DISTINCT FROM
    (to_jsonb(OLD) - ARRAY['status','completed_at','updated_at'])
    OR NEW.status NOT IN ('planned','completed')
  ) THEN
    RAISE EXCEPTION 'Immutable roadmap recommendation' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
-- statement-break
CREATE TRIGGER personal_roadmap_item_guard BEFORE UPDATE ON roadmap_items
FOR EACH ROW EXECUTE FUNCTION personal_roadmap_item_guard();
