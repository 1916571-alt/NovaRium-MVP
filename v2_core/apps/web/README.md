# NovaRium V2 Web Shell

## Run

```bash
cd v2_core/apps/web
npm install
npm run dev
```

Playwright smoke:
```bash
cd v2_core/apps/web
npm install
npx playwright install --with-deps chromium
npm run smoke:test
```
Includes:
- login/nav smoke
- onboarding + analytics bootstrap path smoke (API mocked)

Set API base if needed:

```bash
set NEXT_PUBLIC_API_BASE=http://localhost:8100/v2
```

## Pages

- `/`
  - quick onboarding supports template selection (commerce/content/saas)
  - deterministic seed presets: beginner/standard/advanced
  - optional starter SQL challenge seeding on bootstrap
  - shows latest bootstrap summary (workspace/project/experiment/run)
- `/login`
- `/workspaces`
  - includes per-workspace simulation retention policy update (days)
  - includes workspace retention audit log view + filters (actor/date range)
- `/sql`
  - includes challenge authoring/submission and snippet save/load/update/delete + tag/search/pin filters
- `/experiments`
  - includes variant management (key/weight/config CRUD)
- `/analytics`
  - supports project setup templates: commerce/content/saas
  - deterministic seed presets: beginner/standard/advanced
  - funnel overview follows selected template step plan
  - bootstrap can seed starter SQL challenges by template
- `/scenarios`
  - export scenario pack by project (`scenario-pack-v1` or native `scenario-pack-v2`)
  - import scenario pack into target workspace as a new project (`scenario-pack-v1` and `scenario-pack-v2`)
  - validate-only import check before applying
  - create/revoke/resolve signed share tokens with expiry
  - import payload preview and delta summary vs last export
- `/journey`
- `/community`

Write actions are role-aware in UI:
- `owner/editor`: create/update/delete/activate/bootstrap actions enabled
- `viewer`: read/query actions only

Shared permission UI components:
- `components/RoleBadge.jsx`
- `components/PermissionHint.jsx`

Deep-link prefill supported (query params):
- `workspace_id`, `project_id`, `experiment_id`, `run_id`, `template`, `seed_preset`

## Event Ingest Convention

Use `POST /v2/events/ingest` with batch payload shape:
- `{ "items": [ ... ] }`

Recommended client-side idempotency key rule:
- format: `{project_id}:{session_id}:{seq}:{event_name}`
- `session_id`: browser-tab session ID (fixed during tab lifetime)
- `seq`: per-session increasing integer
- retries must reuse the same `idempotency_key`

Utility helpers:
- `lib/events.js`
  - `buildEventItem(...)`
  - `buildIdempotencyKey(...)`

Example:

```javascript
import { api } from "@/lib/api";
import { buildEventItem } from "@/lib/events";

const item = buildEventItem({
  projectId: "00000000-0000-0000-0000-000000000010",
  userKey: "anon_u_123",
  eventName: "view_home",
  props: { page_path: "/" }
});

await api.ingestEvents([item]);
```
