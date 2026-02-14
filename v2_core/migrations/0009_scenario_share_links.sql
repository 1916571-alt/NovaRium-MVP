create table if not exists scenario_share_links (
    id uuid primary key,
    token_hash text not null unique,
    created_by_user_id uuid not null references users(id) on delete cascade,
    source_project_id uuid not null references projects(id) on delete cascade,
    source_project_name text not null,
    schema_version text not null check (schema_version in ('scenario-pack-v1', 'scenario-pack-v2')),
    payload_json jsonb not null,
    expires_at timestamptz not null,
    last_accessed_at timestamptz,
    created_at timestamptz not null default now()
);

create index if not exists idx_scenario_share_links_expires_at
on scenario_share_links(expires_at);
