alter table variants enable row level security;
alter table variants force row level security;

drop policy if exists variants_rw_policy on variants;

create policy variants_rw_policy on variants
using (
    exists (
        select 1
        from experiments e
        join projects p on p.id = e.project_id
        where e.id = variants.experiment_id
          and app.is_workspace_member(p.workspace_id)
    )
)
with check (
    exists (
        select 1
        from experiments e
        join projects p on p.id = e.project_id
        where e.id = variants.experiment_id
          and app.is_workspace_editor(p.workspace_id)
    )
);
