# NovaRium V2 Foundation Architecture

## 1. Goal
- Build a production-grade, multi-user experimentation platform.
- Keep current MVP as a sandbox, and build V2 core with clean boundaries.
- Support this end-to-end flow:
  1. Simulated platform and event generation
  2. SQL-based problem discovery
  3. Funnel bottleneck diagnosis
  4. Virtual experiment execution and decision
  5. Adoption rollout and user-specific endpoint outcomes (mini-home)

## 2. Product Scope (V2)
- Must have:
  - User authentication
  - Workspace/project ownership model
  - Event ingestion and data marts
  - Experiment design/run/analyze/adopt loop
  - Per-user journey timeline and divergent outcomes
- Not in first release:
  - Billing/payments
  - External SSO enterprise connectors
  - Full real-time streaming pipeline

## 3. Architecture Strategy
- Decision: **Rebuild + Incremental Migration**
- Why:
  - Current MVP has strong domain logic but mixed DB paths/schema contracts.
  - Authentication and authorization should not be retrofitted on unstable data contracts.
  - V2 needs clear bounded contexts and tenant safety from day one.

## 4. Bounded Contexts
- `identity`: users, auth sessions, roles
- `workspace`: teams, projects, ownership
- `event-core`: assignment/events ingestion and query
- `analytics`: marts, funnel, bottleneck detection
- `experimentation`: hypothesis, metrics, guardrails, decisions
- `adoption`: feature rollout states and rollout history
- `journey`: user-specific timeline and endpoint state

## 5. High-Level System
- Frontend: Next.js (app router) + shared chart components
- API: FastAPI (domain service layer + validation)
- DB: PostgreSQL (Supabase managed)
- Auth: Supabase Auth + JWT + Postgres RLS
- Jobs:
  - Celery/Arq worker for ETL, backfills, batch simulation
  - Scheduler for hourly/daily mart refresh

## 6. Data Model (Core Tables)
- `users(id, email, created_at, status)`
- `workspaces(id, owner_user_id, name, created_at)`
- `workspace_members(workspace_id, user_id, role, joined_at)`
- `projects(id, workspace_id, name, created_at)`
- `experiments(id, project_id, hypothesis, primary_metric, status, created_at, started_at, ended_at)`
- `variants(id, experiment_id, key, config_json, traffic_weight)`
- `assignments(id, experiment_id, user_key, variant_key, assigned_at, run_id, weight)`
- `events(id, project_id, experiment_id, user_key, event_name, event_time, value, props_json, run_id)`
- `funnel_definitions(id, project_id, name, steps_json, created_at)`
- `funnel_results(id, funnel_id, run_date, step_index, users, conversion_rate, dropoff_rate)`
- `adoptions(id, experiment_id, winning_variant_key, traffic_percentage, adopted_at, rolled_back_at)`
- `feature_states(id, project_id, feature_key, state_json, updated_at)`
- `user_journeys(id, user_id, project_id, start_state_json, current_state_json, updated_at)`
- `journey_events(id, journey_id, event_type, payload_json, created_at)`

## 7. Event Taxonomy (Standard)
- Required event names:
  - `session_start`
  - `view_home`
  - `view_detail`
  - `click_cta`
  - `add_to_cart`
  - `start_checkout`
  - `purchase`
  - `bounce`
- Rules:
  - One canonical name per semantic action
  - Event schema version field in `props_json`
  - No ad-hoc aliases like mixed `click_banner` / `banner_A`

## 8. API Contract (V2 Minimal)
- Auth
  - `POST /v2/auth/sign-up`
  - `POST /v2/auth/sign-in`
  - `POST /v2/auth/sign-out`
- Projects and experiments
  - `POST /v2/projects`
  - `POST /v2/experiments`
  - `POST /v2/experiments/{id}/activate`
  - `POST /v2/experiments/{id}/deactivate`
- Data and analytics
  - `POST /v2/events/ingest`
  - `POST /v2/funnels/{id}/compute`
  - `GET /v2/funnels/{id}/latest`
  - `GET /v2/experiments/{id}/analysis`
- Adoption and journey
  - `POST /v2/adoptions`
  - `POST /v2/adoptions/{id}/rollout`
  - `POST /v2/adoptions/{id}/rollback`
  - `GET /v2/users/{id}/journey`

## 9. Security and Tenant Isolation
- JWT required for all `/v2/*` except auth endpoints.
- RLS policies enforce:
  - user can only read/write within authorized workspace/project
  - experiment/adoption writes only by editor/admin roles
- Server-side validation:
  - strict enum checks for metric/event names
  - SQL parameter binding only (no f-string SQL for user values)

## 10. Migration Plan from Current MVP
- Phase M1:
  - Freeze current MVP as `legacy-mvp`
  - Keep existing demos alive
- Phase M2:
  - Create V2 schema in PostgreSQL
  - Build compatibility ETL to map old events to new taxonomy
- Phase M3:
  - Port stable domain modules:
    - statistical functions
    - persona behavior logic
  - Rewrite query paths and persistence adapters
- Phase M4:
  - Switch frontend to V2 endpoints
  - Retire old mixed-path DuckDB write coordination

## 11. 4-Week Execution Plan
- Week 1:
  - Finalize ERD and API contracts
  - Implement auth, workspace, project boundaries
  - Add RLS policies and integration tests
- Week 2:
  - Implement event ingest, marts, funnel computation
  - Add bottleneck detection heuristics
- Week 3:
  - Implement experiment lifecycle and adoption rollout
  - Build decision UI and audit timeline
- Week 4:
  - Implement mini-home journey endpoints
  - Harden observability, load tests, release checklist

## 12. Definition of Done (V2 MVP)
- A new user can sign in and create a project.
- Simulated traffic generates standardized events.
- SQL and funnel views identify bottleneck step and segment.
- Experiment can be activated, analyzed, and adopted.
- Adoption changes user endpoint state, and journey diverges per user.

## 13. External References (for implementation standards)
- Supabase JWT/Auth:
  - https://supabase.com/docs/guides/auth/jwts
- Supabase Postgres RLS:
  - https://supabase.com/docs/guides/database/postgres/row-level-security
- FastAPI JWT pattern:
  - https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- OpenFeature reference:
  - https://openfeature.dev/docs/reference/intro
  - https://openfeature.dev/specification/sections/flag-evaluation

## 14. Note on `ijin/aidlc-cc-plugin`
- `https://github.com/ijin/aidlc-cc-plugin` was not publicly discoverable during lookup.
- Treat it as optional until repository visibility/link is confirmed.
- We can still adopt AIDLC-style process gates in this architecture.
