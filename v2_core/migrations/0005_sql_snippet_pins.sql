alter table sql_snippets
add column if not exists is_pinned boolean not null default false;

alter table sql_snippets
add column if not exists pinned_at timestamptz;

create index if not exists idx_sql_snippets_pinned
on sql_snippets (project_id, is_pinned, pinned_at desc, updated_at desc);
