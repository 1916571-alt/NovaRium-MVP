# NovaRium V2 Core

This folder is the V2 core scaffold for production architecture.

Web shell:
- `apps/web` (Next.js app router)

## Quick start

```bash
cd v2_core
python -m venv .venv
.venv\\Scripts\\activate
pip install -e .[dev]
python scripts/apply_migrations.py
uvicorn apps.api.main:app --reload --port 8100
```

Frontend:
```bash
cd apps/web
npm install
npm run dev
```

Integration test (real PostgreSQL + RLS):
```bash
set RUN_DB_INTEGRATION=1
pytest -q tests/test_rls_integration.py
```

Full E2E flow (real PostgreSQL):
```bash
set RUN_DB_INTEGRATION=1
pytest -q tests/test_e2e_flow_integration.py
```

Smoke flow (migrations + RLS + E2E in one command):
```bash
set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
python scripts/smoke_flow.py
```

Cleanup stale simulations (dry-run / apply):
```bash
python scripts/cleanup_stale_simulations.py --retention-days 30
python scripts/cleanup_stale_simulations.py --retention-days 30 --apply
python scripts/cleanup_stale_simulations.py --retention-days 30 --respect-workspace-policy --apply
```

## Endpoints

- `GET /v2/health`
- `POST /v2/auth/sign-up`
- `POST /v2/auth/sign-in`
- `POST /v2/auth/refresh`
- `POST /v2/auth/sign-out`
- `GET /v2/auth/me`
- `GET /v2/workspaces`
- `POST /v2/workspaces`
- `POST /v2/workspaces/{workspace_id}/members`
- `PUT /v2/workspaces/{workspace_id}/retention`
- `GET /v2/workspaces/{workspace_id}/retention-audit`
  - query: `limit`, `changed_by_user_id`, `changed_at_from`, `changed_at_to`
- `GET /v2/projects`
- `POST /v2/projects`
- `GET /v2/experiments`
- `POST /v2/experiments`
- `POST /v2/experiments/{experiment_id}/activate`
- `POST /v2/experiments/{experiment_id}/deactivate`
- `GET /v2/experiments/{experiment_id}/variants`
- `POST /v2/experiments/{experiment_id}/variants`
- `PUT /v2/experiments/{experiment_id}/variants/{variant_key}`
- `DELETE /v2/experiments/{experiment_id}/variants/{variant_key}`
- `GET /v2/experiments/{experiment_id}/analysis?run_id=...`
- `POST /v2/experiments/{experiment_id}/analysis/persist?run_id=...`
- `POST /v2/experiments/{experiment_id}/adopt-from-analysis?run_id=...`
- `POST /v2/adoptions`
- `POST /v2/adoptions/{adoption_id}/rollout`
- `POST /v2/adoptions/{adoption_id}/rollback`
- `GET /v2/journeys/me?project_id=...`
- `GET /v2/community/posts`
  - query: `sort_by=recent|ranked`
- `POST /v2/community/posts`
- `GET /v2/community/posts/{post_id}/comments`
- `POST /v2/community/posts/{post_id}/comments`
- `POST /v2/community/forks`
- `GET /v2/portfolio/me`
- `GET /v2/analytics/templates`
- `POST /v2/analytics/projects/{project_id}/bootstrap`
- `GET /v2/analytics/projects/{project_id}/funnel`
  - query: `run_id`, `experiment_id`, `template`
- `GET /v2/scenarios/export`
  - query: `project_id`, `schema_version=scenario-pack-v1|scenario-pack-v2`
- `POST /v2/scenarios/import`
  - body `schema_version`: `scenario-pack-v1|scenario-pack-v2`
- `POST /v2/scenarios/import/validate`
- `POST /v2/scenarios/shares`
- `GET /v2/scenarios/shares/{share_token}`
- `POST /v2/sql/execute`
- `GET /v2/sql/challenges`
- `POST /v2/sql/challenges`
- `POST /v2/sql/challenges/{challenge_id}/submit`

`GET /v2/workspaces`, `GET /v2/projects`, `GET /v2/experiments` responses include `my_role` for role-aware UI.
`GET /v2/workspaces` also includes `simulation_retention_days` (1..365).
- `GET /v2/sql/snippets`
  - query: `project_id`, `q`, `tag`, `pinned_only`
- `POST /v2/sql/snippets`
- `PUT /v2/sql/snippets/{snippet_id}`
- `DELETE /v2/sql/snippets/{snippet_id}`

`/v2/sql/challenges/{challenge_id}/submit` currently performs MVP grading using:
- `expected_schema.columns` exact match
- `expected_metrics.row_count` match
- `expected_metrics.must_have_columns` containment
- `expected_metrics.expected_rows` comparison (unordered by default)
- `expected_metrics.numeric_tolerance` for numeric row matching

`/v2/analytics/projects/{project_id}/bootstrap` supports setup templates:
- `template=commerce|content|saas`
  - `seed_preset=beginner|standard|advanced` (deterministic defaults)
  - template-specific step plans are also used in funnel overview
  - optional `seed_sql_challenges=true|false` for starter SQL challenge seeding

## Environment

Copy `.env.example` to `.env` and set values.
For signed share links, set `SCENARIO_SHARE_SECRET` (falls back to `SUPABASE_JWT_SECRET` if omitted).

CI:
- GitHub Actions workflow: `.github/workflows/v2-tests.yml`
- GitHub Actions workflow: `.github/workflows/v2-web-smoke.yml`
- GitHub Actions workflow: `.github/workflows/v2-cleanup-simulations.yml` (requires `V2_DATABASE_URL` secret)
