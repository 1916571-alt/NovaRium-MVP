create table if not exists sql_snippets (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references projects(id) on delete cascade,
    author_user_id uuid not null references users(id) on delete cascade,
    title text not null,
    sql_text text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_sql_snippets_project_id on sql_snippets(project_id);
create index if not exists idx_sql_snippets_created_at on sql_snippets(created_at desc);

alter table sql_snippets enable row level security;
alter table sql_snippets force row level security;

drop policy if exists sql_snippets_select_policy on sql_snippets;
drop policy if exists sql_snippets_insert_policy on sql_snippets;
drop policy if exists sql_snippets_update_delete_policy on sql_snippets;
drop policy if exists sql_snippets_rw_policy on sql_snippets;

create policy sql_snippets_select_policy on sql_snippets
for select using (
    exists (
        select 1
        from projects p
        where p.id = sql_snippets.project_id
          and app.is_workspace_member(p.workspace_id)
    )
);

create policy sql_snippets_insert_policy on sql_snippets
for insert with check (
    exists (
        select 1
        from projects p
        where p.id = sql_snippets.project_id
          and app.is_workspace_editor(p.workspace_id)
    )
    and sql_snippets.author_user_id = app.current_user_id()
);

create policy sql_snippets_update_delete_policy on sql_snippets
for update using (
    exists (
        select 1
        from projects p
        where p.id = sql_snippets.project_id
          and app.is_workspace_editor(p.workspace_id)
    )
) with check (
    exists (
        select 1
        from projects p
        where p.id = sql_snippets.project_id
          and app.is_workspace_editor(p.workspace_id)
    )
);

create policy sql_snippets_delete_policy on sql_snippets
for delete using (
    exists (
        select 1
        from projects p
        where p.id = sql_snippets.project_id
          and app.is_workspace_editor(p.workspace_id)
    )
);
