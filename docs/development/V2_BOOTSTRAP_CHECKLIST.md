# V2 Bootstrap Checklist (Day 1-7)

## Day 1: Repo and Runtime Baseline
- Create new repository for V2 core (`novarium-v2-core`).
- Set Python version and package manager (`pyproject.toml` + lockfile).
- Create base folders:
  - `apps/api`
  - `apps/web`
  - `packages/domain`
  - `packages/db`
  - `infra`
- Add CI baseline:
  - lint
  - type check
  - unit tests

## Day 2: Database Foundation
- Provision Supabase project.
- Create initial schema:
  - `users`
  - `workspaces`
  - `workspace_members`
  - `projects`
  - `experiments`
  - `variants`
  - `assignments`
  - `events`
  - `adoptions`
  - `user_journeys`
- Add migration tool and first migration script.
- Add index strategy for `events(project_id, event_time)` and `assignments(experiment_id, run_id)`.

## Day 3: Auth and Access Control
- Enable Supabase Auth.
- Implement JWT verification middleware in API.
- Add RLS policies for workspace/project scoping.
- Add integration tests for:
  - unauthorized access blocked
  - cross-workspace access blocked

## Day 4: Event Ingestion and Validation
- Implement `POST /v2/events/ingest`.
- Enforce canonical event names (`session_start`, `view_home`, `click_cta`, `purchase`, etc.).
- Enforce payload schema version in `props_json`.
- Add dead-letter logging for invalid events.

## Day 5: Funnel and Bottleneck
- Implement funnel definition and compute endpoints.
- Materialize daily funnel results table.
- Add bottleneck detector:
  - step dropoff threshold
  - segment anomaly threshold
- Add SQL templates in UI for root cause queries.

## Day 6: Experiment and Adoption Loop
- Implement experiment activate/deactivate APIs.
- Implement analysis endpoint:
  - conversion
  - lift
  - p-value
  - guardrails
- Implement adoption rollout and rollback APIs.

## Day 7: Divergent Journey (Mini-home MVP)
- Implement per-user journey state updates on adoption.
- Build minimal timeline endpoint (`GET /v2/users/{id}/journey`).
- Render different endpoint states from same origin based on adoption path.

## Exit Criteria for Week 1
- Auth + RLS works in production-like environment.
- Event ingestion and funnel computation are queryable.
- One experiment can run to decision and adoption.
- At least one user journey divergence scenario is visible end-to-end.
