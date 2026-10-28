-- Operator-reviewed after additive migration, with separately created LOGIN roles.
-- Never store passwords here. Runtime roles cannot own tables or perform DDL.
-- Role defaults survive Neon transaction pooling. Startup options / SET do not.
ALTER ROLE interview_prep_auth SET search_path = auth;
ALTER ROLE interview_prep_auth SET statement_timeout = '10s';
ALTER ROLE interview_prep_auth SET timezone = 'UTC';
ALTER ROLE interview_prep_runtime SET timezone = 'UTC';
REVOKE ALL ON SCHEMA auth FROM PUBLIC;
REVOKE CREATE ON SCHEMA auth FROM interview_prep_auth, interview_prep_runtime;
GRANT USAGE ON SCHEMA auth TO interview_prep_auth, interview_prep_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
  auth."user", auth.session, auth.account, auth.verification, auth.jwks, auth.request_limits
TO interview_prep_auth;
REVOKE ALL ON TABLE
  auth."user", auth.session, auth.account, auth.verification, auth.jwks, auth.request_limits
FROM interview_prep_runtime;
GRANT SELECT ON auth.api_sessions TO interview_prep_runtime;

