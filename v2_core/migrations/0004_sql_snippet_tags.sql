alter table sql_snippets
add column if not exists tags text[] not null default '{}';

create index if not exists idx_sql_snippets_tags_gin on sql_snippets using gin (tags);
