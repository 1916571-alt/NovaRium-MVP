create table if not exists platform_events_raw (
    id bigserial primary key,
    event_id uuid not null unique,
    event_name text not null,
    event_time timestamptz not null default now(),
    client_ts timestamptz,
    user_id uuid not null references users(id) on delete cascade,
    workspace_id uuid references workspaces(id) on delete set null,
    project_id uuid references projects(id) on delete set null,
    session_id text,
    page_path text,
    props_json jsonb not null default '{}'::jsonb,
    received_at timestamptz not null default now()
);

create index if not exists idx_platform_events_raw_event_time
on platform_events_raw(event_time desc);

create index if not exists idx_platform_events_raw_workspace_event_time
on platform_events_raw(workspace_id, event_time desc);

create index if not exists idx_platform_events_raw_project_event_time
on platform_events_raw(project_id, event_time desc);

create index if not exists idx_platform_events_raw_event_name_time
on platform_events_raw(event_name, event_time desc);

create table if not exists platform_event_daily_metrics (
    event_date date not null,
    workspace_id uuid,
    project_id uuid,
    event_name text not null,
    events_count bigint not null,
    users_count bigint not null,
    sessions_count bigint not null,
    computed_at timestamptz not null default now(),
    primary key (event_date, workspace_id, project_id, event_name)
);

create index if not exists idx_platform_event_daily_metrics_event_date
on platform_event_daily_metrics(event_date desc);

alter table platform_events_raw enable row level security;
alter table platform_events_raw force row level security;
alter table platform_event_daily_metrics enable row level security;
alter table platform_event_daily_metrics force row level security;

drop policy if exists platform_events_raw_rw_policy on platform_events_raw;
drop policy if exists platform_event_daily_metrics_select_policy on platform_event_daily_metrics;

create policy platform_events_raw_rw_policy on platform_events_raw
using (
    user_id = app.current_user_id()
    or (
        workspace_id is not null
        and app.is_workspace_member(workspace_id)
    )
)
with check (
    user_id = app.current_user_id()
    and (
        workspace_id is null
        or app.is_workspace_member(workspace_id)
    )
);

create policy platform_event_daily_metrics_select_policy on platform_event_daily_metrics
for select using (
    workspace_id is null
    or app.is_workspace_member(workspace_id)
);
