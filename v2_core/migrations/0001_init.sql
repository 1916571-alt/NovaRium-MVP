-- NovaRium V2 PostgreSQL DDL v1
-- Target: Supabase PostgreSQL

create extension if not exists "pgcrypto";

-- =====================================================
-- Core Identity / Workspace
-- =====================================================

create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    email text not null unique,
    display_name text,
    status text not null default 'active',
    created_at timestamptz not null default now()
);

create table if not exists workspaces (
    id uuid primary key default gen_random_uuid(),
    owner_user_id uuid not null references users(id) on delete cascade,
    name text not null,
    created_at timestamptz not null default now()
);

create table if not exists workspace_members (
    workspace_id uuid not null references workspaces(id) on delete cascade,
    user_id uuid not null references users(id) on delete cascade,
    role text not null check (role in ('owner', 'editor', 'viewer')),
    joined_at timestamptz not null default now(),
    primary key (workspace_id, user_id)
);

create table if not exists projects (
    id uuid primary key default gen_random_uuid(),
    workspace_id uuid not null references workspaces(id) on delete cascade,
    name text not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_projects_workspace_id on projects(workspace_id);

-- =====================================================
-- Experimentation
-- =====================================================

create table if not exists experiments (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references projects(id) on delete cascade,
    hypothesis text not null,
    primary_metric text not null,
    guardrail_metrics jsonb not null default '[]'::jsonb,
    status text not null check (status in ('draft', 'active', 'completed', 'archived')) default 'draft',
    created_by uuid not null references users(id),
    created_at timestamptz not null default now(),
    started_at timestamptz,
    ended_at timestamptz
);

create index if not exists idx_experiments_project_id on experiments(project_id);
create index if not exists idx_experiments_status on experiments(status);

create table if not exists variants (
    id uuid primary key default gen_random_uuid(),
    experiment_id uuid not null references experiments(id) on delete cascade,
    variant_key text not null,
    config_json jsonb not null default '{}'::jsonb,
    traffic_weight numeric(5,2) not null default 50.00,
    unique (experiment_id, variant_key)
);

create table if not exists assignments (
    id bigserial primary key,
    project_id uuid not null references projects(id) on delete cascade,
    experiment_id uuid not null references experiments(id) on delete cascade,
    user_key text not null,
    variant_key text not null,
    assigned_at timestamptz not null default now(),
    run_id text not null,
    weight numeric(10,4) not null default 1.0
);

create index if not exists idx_assignments_exp_run on assignments(experiment_id, run_id);
create index if not exists idx_assignments_project_time on assignments(project_id, assigned_at);

create table if not exists experiment_results (
    id bigserial primary key,
    experiment_id uuid not null references experiments(id) on delete cascade,
    run_id text not null,
    control_users int not null default 0,
    control_conversions int not null default 0,
    test_users int not null default 0,
    test_conversions int not null default 0,
    lift numeric(10,6),
    p_value numeric(12,10),
    ci_lower numeric(10,6),
    ci_upper numeric(10,6),
    srm_p_value numeric(12,10),
    decision text,
    decided_by uuid references users(id),
    decided_at timestamptz,
    created_at timestamptz not null default now(),
    unique (experiment_id, run_id)
);

-- =====================================================
-- Event Core / Analytics
-- =====================================================

create table if not exists events (
    id bigserial primary key,
    project_id uuid not null references projects(id) on delete cascade,
    experiment_id uuid references experiments(id) on delete set null,
    user_key text not null,
    run_id text,
    event_name text not null check (
        event_name in (
            'session_start',
            'view_home',
            'view_detail',
            'click_cta',
            'add_to_cart',
            'start_checkout',
            'purchase',
            'bounce'
        )
    ),
    event_time timestamptz not null default now(),
    value numeric(14,2) not null default 0,
    props_json jsonb not null default '{}'::jsonb
);

create index if not exists idx_events_project_time on events(project_id, event_time);
create index if not exists idx_events_project_event_time on events(project_id, event_name, event_time);
create index if not exists idx_events_run_id on events(run_id);

create table if not exists funnel_definitions (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references projects(id) on delete cascade,
    name text not null,
    steps_json jsonb not null,
    created_by uuid not null references users(id),
    created_at timestamptz not null default now()
);

create index if not exists idx_funnel_def_project_id on funnel_definitions(project_id);

create table if not exists funnel_results (
    id bigserial primary key,
    funnel_id uuid not null references funnel_definitions(id) on delete cascade,
    run_date date not null,
    step_index int not null,
    step_name text not null,
    users_count int not null,
    conversion_rate numeric(10,6) not null,
    dropoff_rate numeric(10,6) not null,
    computed_at timestamptz not null default now(),
    unique (funnel_id, run_date, step_index)
);

-- =====================================================
-- Adoption / Minihome
-- =====================================================

create table if not exists adoptions (
    id bigserial primary key,
    experiment_id uuid not null references experiments(id) on delete cascade,
    winning_variant_key text not null,
    traffic_percentage numeric(5,2) not null default 100.00 check (traffic_percentage >= 0 and traffic_percentage <= 100),
    reason text,
    adopted_by uuid not null references users(id),
    adopted_at timestamptz not null default now(),
    rolled_back_at timestamptz
);

create table if not exists feature_states (
    id bigserial primary key,
    project_id uuid not null references projects(id) on delete cascade,
    feature_key text not null,
    state_json jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now(),
    unique (project_id, feature_key)
);

create table if not exists user_journeys (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    project_id uuid not null references projects(id) on delete cascade,
    start_state_json jsonb not null default '{}'::jsonb,
    current_state_json jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now(),
    unique (user_id, project_id)
);

create table if not exists journey_patches (
    id bigserial primary key,
    journey_id uuid not null references user_journeys(id) on delete cascade,
    source_type text not null check (source_type in ('adoption', 'manual', 'system')),
    source_id text,
    patch_json jsonb not null,
    created_at timestamptz not null default now()
);

create table if not exists journey_events (
    id bigserial primary key,
    journey_id uuid not null references user_journeys(id) on delete cascade,
    event_type text not null,
    payload_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

-- =====================================================
-- Community
-- =====================================================

create table if not exists community_posts (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references projects(id) on delete cascade,
    experiment_id uuid references experiments(id) on delete set null,
    author_user_id uuid not null references users(id),
    title text not null,
    body_md text not null,
    tags text[] not null default '{}',
    created_at timestamptz not null default now()
);

create index if not exists idx_community_posts_project_id on community_posts(project_id);
create index if not exists idx_community_posts_created_at on community_posts(created_at desc);

create table if not exists community_comments (
    id bigserial primary key,
    post_id uuid not null references community_posts(id) on delete cascade,
    author_user_id uuid not null references users(id),
    body_md text not null,
    created_at timestamptz not null default now()
);

create table if not exists experiment_forks (
    id bigserial primary key,
    source_experiment_id uuid not null references experiments(id) on delete cascade,
    forked_experiment_id uuid not null references experiments(id) on delete cascade,
    forked_by uuid not null references users(id),
    created_at timestamptz not null default now()
);

-- =====================================================
-- SQL Learning
-- =====================================================

create table if not exists sql_challenges (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references projects(id) on delete cascade,
    title text not null,
    prompt_md text not null,
    difficulty text not null check (difficulty in ('easy', 'medium', 'hard')),
    expected_schema jsonb not null default '{}'::jsonb,
    expected_metrics jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists sql_submissions (
    id bigserial primary key,
    challenge_id uuid not null references sql_challenges(id) on delete cascade,
    user_id uuid not null references users(id) on delete cascade,
    sql_text text not null,
    is_correct boolean not null default false,
    feedback_json jsonb not null default '{}'::jsonb,
    submitted_at timestamptz not null default now()
);
