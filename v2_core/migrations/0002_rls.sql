-- NovaRium V2 RLS policy baseline
-- Uses request.jwt.claim.sub claim injected by API connection layer.

create schema if not exists app;

create or replace function app.current_user_id()
returns uuid
language plpgsql
stable
as $$
declare
    v_sub text;
begin
    v_sub := current_setting('request.jwt.claim.sub', true);
    if v_sub is null or length(trim(v_sub)) = 0 then
        return null;
    end if;
    begin
        return v_sub::uuid;
    exception when others then
        return null;
    end;
end;
$$;

create or replace function app.is_workspace_member(p_workspace_id uuid)
returns boolean
language sql
stable
as $$
    select exists (
        select 1
        from workspace_members wm
        where wm.workspace_id = p_workspace_id
          and wm.user_id = app.current_user_id()
    );
$$;

create or replace function app.is_workspace_editor(p_workspace_id uuid)
returns boolean
language sql
stable
as $$
    select exists (
        select 1
        from workspace_members wm
        where wm.workspace_id = p_workspace_id
          and wm.user_id = app.current_user_id()
          and wm.role in ('owner', 'editor')
    );
$$;

-- Enable + force RLS
alter table workspaces enable row level security;
alter table workspace_members enable row level security;
alter table projects enable row level security;
alter table experiments enable row level security;
alter table events enable row level security;
alter table adoptions enable row level security;
alter table feature_states enable row level security;
alter table user_journeys enable row level security;
alter table journey_patches enable row level security;
alter table journey_events enable row level security;
alter table community_posts enable row level security;
alter table community_comments enable row level security;
alter table experiment_forks enable row level security;
alter table sql_challenges enable row level security;
alter table sql_submissions enable row level security;

alter table workspaces force row level security;
alter table workspace_members force row level security;
alter table projects force row level security;
alter table experiments force row level security;
alter table events force row level security;
alter table adoptions force row level security;
alter table feature_states force row level security;
alter table user_journeys force row level security;
alter table journey_patches force row level security;
alter table journey_events force row level security;
alter table community_posts force row level security;
alter table community_comments force row level security;
alter table experiment_forks force row level security;
alter table sql_challenges force row level security;
alter table sql_submissions force row level security;

-- Remove old policies safely
drop policy if exists workspaces_select_policy on workspaces;
drop policy if exists workspaces_insert_policy on workspaces;
drop policy if exists workspaces_update_policy on workspaces;
drop policy if exists workspaces_delete_policy on workspaces;
drop policy if exists workspace_members_select_policy on workspace_members;
drop policy if exists workspace_members_insert_owner_policy on workspace_members;
drop policy if exists workspace_members_update_policy on workspace_members;
drop policy if exists workspace_members_delete_policy on workspace_members;
drop policy if exists projects_select_policy on projects;
drop policy if exists projects_insert_policy on projects;
drop policy if exists projects_update_policy on projects;
drop policy if exists projects_delete_policy on projects;
drop policy if exists experiments_rw_policy on experiments;
drop policy if exists events_rw_policy on events;
drop policy if exists adoptions_rw_policy on adoptions;
drop policy if exists feature_states_rw_policy on feature_states;
drop policy if exists user_journeys_rw_policy on user_journeys;
drop policy if exists journey_patches_rw_policy on journey_patches;
drop policy if exists journey_events_rw_policy on journey_events;
drop policy if exists community_posts_rw_policy on community_posts;
drop policy if exists community_comments_rw_policy on community_comments;
drop policy if exists experiment_forks_rw_policy on experiment_forks;
drop policy if exists sql_challenges_rw_policy on sql_challenges;
drop policy if exists sql_submissions_rw_policy on sql_submissions;

-- Workspaces
create policy workspaces_select_policy on workspaces
for select using (
    app.is_workspace_member(id)
);

create policy workspaces_insert_policy on workspaces
for insert with check (
    owner_user_id = app.current_user_id()
);

create policy workspaces_update_policy on workspaces
for update using (
    owner_user_id = app.current_user_id()
);

create policy workspaces_delete_policy on workspaces
for delete using (
    owner_user_id = app.current_user_id()
);

-- Workspace members
create policy workspace_members_select_policy on workspace_members
for select using (
    app.is_workspace_member(workspace_id)
);

create policy workspace_members_insert_owner_policy on workspace_members
for insert with check (
    app.is_workspace_editor(workspace_id)
    or (
        role = 'owner'
        and user_id = app.current_user_id()
        and exists (
            select 1
            from workspaces w
            where w.id = workspace_members.workspace_id
              and w.owner_user_id = app.current_user_id()
        )
    )
);

create policy workspace_members_update_policy on workspace_members
for update using (
    app.is_workspace_editor(workspace_id)
);

create policy workspace_members_delete_policy on workspace_members
for delete using (
    app.is_workspace_editor(workspace_id)
);

-- Projects
create policy projects_select_policy on projects
for select using (
    app.is_workspace_member(workspace_id)
);

create policy projects_insert_policy on projects
for insert with check (
    app.is_workspace_editor(workspace_id)
);

create policy projects_update_policy on projects
for update using (
    app.is_workspace_editor(workspace_id)
);

create policy projects_delete_policy on projects
for delete using (
    app.is_workspace_editor(workspace_id)
);

-- Experiments
create policy experiments_rw_policy on experiments
using (
    exists (
        select 1
        from projects p
        where p.id = experiments.project_id
          and app.is_workspace_member(p.workspace_id)
    )
)
with check (
    exists (
        select 1
        from projects p
        where p.id = experiments.project_id
          and app.is_workspace_editor(p.workspace_id)
    )
);

-- Events
create policy events_rw_policy on events
using (
    exists (
        select 1
        from projects p
        where p.id = events.project_id
          and app.is_workspace_member(p.workspace_id)
    )
)
with check (
    exists (
        select 1
        from projects p
        where p.id = events.project_id
          and app.is_workspace_editor(p.workspace_id)
    )
);

-- Adoptions
create policy adoptions_rw_policy on adoptions
using (
    exists (
        select 1
        from experiments e
        join projects p on p.id = e.project_id
        where e.id = adoptions.experiment_id
          and app.is_workspace_member(p.workspace_id)
    )
)
with check (
    exists (
        select 1
        from experiments e
        join projects p on p.id = e.project_id
        where e.id = adoptions.experiment_id
          and app.is_workspace_editor(p.workspace_id)
    )
);

-- Feature states
create policy feature_states_rw_policy on feature_states
using (
    exists (
        select 1
        from projects p
        where p.id = feature_states.project_id
          and app.is_workspace_member(p.workspace_id)
    )
)
with check (
    exists (
        select 1
        from projects p
        where p.id = feature_states.project_id
          and app.is_workspace_editor(p.workspace_id)
    )
);

-- User journeys
create policy user_journeys_rw_policy on user_journeys
using (
    exists (
        select 1
        from projects p
        where p.id = user_journeys.project_id
          and app.is_workspace_member(p.workspace_id)
    )
)
with check (
    exists (
        select 1
        from projects p
        where p.id = user_journeys.project_id
          and app.is_workspace_editor(p.workspace_id)
    )
);

-- Journey patches
create policy journey_patches_rw_policy on journey_patches
using (
    exists (
        select 1
        from user_journeys j
        join projects p on p.id = j.project_id
        where j.id = journey_patches.journey_id
          and app.is_workspace_member(p.workspace_id)
    )
)
with check (
    exists (
        select 1
        from user_journeys j
        join projects p on p.id = j.project_id
        where j.id = journey_patches.journey_id
          and app.is_workspace_editor(p.workspace_id)
    )
);

-- Journey events
create policy journey_events_rw_policy on journey_events
using (
    exists (
        select 1
        from user_journeys j
        join projects p on p.id = j.project_id
        where j.id = journey_events.journey_id
          and app.is_workspace_member(p.workspace_id)
    )
)
with check (
    exists (
        select 1
        from user_journeys j
        join projects p on p.id = j.project_id
        where j.id = journey_events.journey_id
          and app.is_workspace_editor(p.workspace_id)
    )
);

-- Community posts
create policy community_posts_rw_policy on community_posts
using (
    exists (
        select 1
        from projects p
        where p.id = community_posts.project_id
          and app.is_workspace_member(p.workspace_id)
    )
)
with check (
    exists (
        select 1
        from projects p
        where p.id = community_posts.project_id
          and app.is_workspace_member(p.workspace_id)
    )
);

-- Community comments
create policy community_comments_rw_policy on community_comments
using (
    exists (
        select 1
        from community_posts cp
        join projects p on p.id = cp.project_id
        where cp.id = community_comments.post_id
          and app.is_workspace_member(p.workspace_id)
    )
)
with check (
    exists (
        select 1
        from community_posts cp
        join projects p on p.id = cp.project_id
        where cp.id = community_comments.post_id
          and app.is_workspace_member(p.workspace_id)
    )
);

-- Experiment forks
create policy experiment_forks_rw_policy on experiment_forks
using (
    exists (
        select 1
        from experiments src
        join projects psrc on psrc.id = src.project_id
        where src.id = experiment_forks.source_experiment_id
          and app.is_workspace_member(psrc.workspace_id)
    )
    and exists (
        select 1
        from experiments dst
        join projects pdst on pdst.id = dst.project_id
        where dst.id = experiment_forks.forked_experiment_id
          and app.is_workspace_member(pdst.workspace_id)
    )
)
with check (
    experiment_forks.forked_by = app.current_user_id()
    and exists (
        select 1
        from experiments src
        join projects psrc on psrc.id = src.project_id
        where src.id = experiment_forks.source_experiment_id
          and app.is_workspace_member(psrc.workspace_id)
    )
    and exists (
        select 1
        from experiments dst
        join projects pdst on pdst.id = dst.project_id
        where dst.id = experiment_forks.forked_experiment_id
          and app.is_workspace_member(pdst.workspace_id)
    )
);

-- SQL challenges
create policy sql_challenges_rw_policy on sql_challenges
using (
    exists (
        select 1
        from projects p
        where p.id = sql_challenges.project_id
          and app.is_workspace_member(p.workspace_id)
    )
)
with check (
    exists (
        select 1
        from projects p
        where p.id = sql_challenges.project_id
          and app.is_workspace_editor(p.workspace_id)
    )
);

-- SQL submissions
create policy sql_submissions_rw_policy on sql_submissions
using (
    sql_submissions.user_id = app.current_user_id()
    and exists (
        select 1
        from sql_challenges c
        join projects p on p.id = c.project_id
        where c.id = sql_submissions.challenge_id
          and app.is_workspace_member(p.workspace_id)
    )
)
with check (
    sql_submissions.user_id = app.current_user_id()
    and exists (
        select 1
        from sql_challenges c
        join projects p on p.id = c.project_id
        where c.id = sql_submissions.challenge_id
          and app.is_workspace_member(p.workspace_id)
    )
);
