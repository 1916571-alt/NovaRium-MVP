alter table scenario_share_links
add column if not exists revoked_at timestamptz;

alter table scenario_share_links
add column if not exists revoked_by_user_id uuid references users(id) on delete set null;

create index if not exists idx_scenario_share_links_revoked_at
on scenario_share_links(revoked_at);
