-- Run as the migration/table owner AFTER every migration and catalogue publication.
-- Create the LOGIN role and set its password interactively first; no password in SQL.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO interview_prep_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO interview_prep_runtime;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO interview_prep_runtime;
REVOKE ALL ON TABLE public.alembic_version FROM interview_prep_runtime;
GRANT SELECT ON TABLE public.alembic_version TO interview_prep_runtime;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO interview_prep_runtime;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO interview_prep_runtime;
