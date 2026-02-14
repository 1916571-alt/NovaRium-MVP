create table if not exists workspace_retention_audits (
    id bigserial primary key,
    workspace_id uuid not null references workspaces(id) on delete cascade,
    changed_by_user_id uuid not null references users(id) on delete cascade,
    old_retention_days int not null check (old_retention_days >= 1 and old_retention_days <= 365),
    new_retention_days int not null check (new_retention_days >= 1 and new_retention_days <= 365),
    changed_at timestamptz not null default now()
);

create index if not exists idx_workspace_retention_audits_workspace_changed_at
on workspace_retention_audits(workspace_id, changed_at desc);

alter table workspace_retention_audits enable row level security;
alter table workspace_retention_audits force row level security;

drop policy if exists workspace_retention_audits_select_policy on workspace_retention_audits;
drop policy if exists workspace_retention_audits_insert_policy on workspace_retention_audits;

create policy workspace_retention_audits_select_policy on workspace_retention_audits
for select using (
    app.is_workspace_member(workspace_id)
);

create policy workspace_retention_audits_insert_policy on workspace_retention_audits
for insert with check (
    changed_by_user_id = app.current_user_id()
    and app.is_workspace_editor(workspace_id)
);
