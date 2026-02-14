alter table workspaces
add column if not exists simulation_retention_days int not null default 30
check (simulation_retention_days >= 1 and simulation_retention_days <= 365);
