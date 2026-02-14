# scripts/db

This folder now contains lightweight compatibility wrappers.

- Legacy one-off scripts tied to `novarium_local.db` were moved to:
  - `scripts/legacy/db/`
- Wrappers are kept so old commands in docs do not fail immediately.

For new V2 work, use:
- `v2_core/migrations/0001_init.sql`
- `v2_core/migrations/0002_rls.sql`

