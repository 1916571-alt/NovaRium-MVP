alter table events
add column if not exists idempotency_key text;

alter table events
add column if not exists schema_version text not null default 'event-v1';

alter table events
add column if not exists source text not null default 'sdk';

alter table events
add column if not exists received_at timestamptz not null default now();

create index if not exists idx_events_received_at
on events(received_at desc);

create unique index if not exists uq_events_project_idempotency
on events(project_id, idempotency_key);
