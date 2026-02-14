import json

from apps.api.db.session import get_db_conn
from apps.api.schemas.experiments import (
    ExperimentCreateRequest,
    VariantCreateRequest,
    VariantUpdateRequest,
)


def list_experiments_for_user(user_id: str, project_id: str | None = None) -> list[dict]:
    where_clause = ""
    params = [user_id]
    if project_id:
        where_clause = "and e.project_id = %s::uuid"
        params.append(project_id)

    sql = f"""
        select
            e.id::text,
            e.project_id::text,
            wm.role,
            e.hypothesis,
            e.primary_metric,
            e.guardrail_metrics,
            e.status,
            e.created_by::text,
            e.created_at::text,
            e.started_at::text,
            e.ended_at::text
        from experiments e
        join projects p on p.id = e.project_id
        join workspace_members wm on wm.workspace_id = p.workspace_id
        where wm.user_id = %s::uuid
        {where_clause}
        order by e.created_at desc
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
    return [
        {
            "id": row[0],
            "project_id": row[1],
            "my_role": row[2],
            "hypothesis": row[3],
            "primary_metric": row[4],
            "guardrail_metrics": row[5] or [],
            "status": row[6],
            "created_by": row[7],
            "created_at": row[8],
            "started_at": row[9],
            "ended_at": row[10],
        }
        for row in rows
    ]


def create_experiment_for_user(user_id: str, body: ExperimentCreateRequest) -> dict:
    sql = """
        insert into experiments (
            project_id, hypothesis, primary_metric, guardrail_metrics, status, created_by
        )
        select %s::uuid, %s, %s, %s::jsonb, 'draft', %s::uuid
        where exists (
            select 1
            from projects p
            join workspace_members wm on wm.workspace_id = p.workspace_id
            where p.id = %s::uuid
              and wm.user_id = %s::uuid
              and wm.role in ('owner', 'editor')
        )
        returning
            id::text,
            project_id::text,
            (
                select wm.role
                from projects p
                join workspace_members wm on wm.workspace_id = p.workspace_id
                where p.id = experiments.project_id
                  and wm.user_id = %s::uuid
                limit 1
            ) as my_role,
            hypothesis,
            primary_metric,
            guardrail_metrics,
            status,
            created_by::text,
            created_at::text,
            started_at::text,
            ended_at::text
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    body.project_id,
                    body.hypothesis,
                    body.primary_metric,
                    json.dumps(body.guardrail_metrics),
                    user_id,
                    body.project_id,
                    user_id,
                    user_id,
                ),
            )
            row = cur.fetchone()
    if not row:
        raise PermissionError("Not allowed to create experiment for this project")
    return {
        "id": row[0],
        "project_id": row[1],
        "my_role": row[2],
        "hypothesis": row[3],
        "primary_metric": row[4],
        "guardrail_metrics": row[5] or [],
        "status": row[6],
        "created_by": row[7],
        "created_at": row[8],
        "started_at": row[9],
        "ended_at": row[10],
    }


def set_experiment_status_for_user(user_id: str, experiment_id: str, active: bool) -> dict:
    if active:
        sql = """
            update experiments e
            set status = 'active', started_at = now(), ended_at = null
            where e.id = %s::uuid
              and exists (
                select 1
                from projects p
                join workspace_members wm on wm.workspace_id = p.workspace_id
                where p.id = e.project_id
                  and wm.user_id = %s::uuid
                  and wm.role in ('owner', 'editor')
              )
            returning
                e.id::text,
                e.project_id::text,
                (
                    select wm.role
                    from projects p
                    join workspace_members wm on wm.workspace_id = p.workspace_id
                    where p.id = e.project_id
                      and wm.user_id = %s::uuid
                    limit 1
                ) as my_role,
                e.hypothesis,
                e.primary_metric,
                e.guardrail_metrics,
                e.status,
                e.created_by::text,
                e.created_at::text,
                e.started_at::text,
                e.ended_at::text
        """
    else:
        sql = """
            update experiments e
            set status = 'completed', ended_at = now()
            where e.id = %s::uuid
              and exists (
                select 1
                from projects p
                join workspace_members wm on wm.workspace_id = p.workspace_id
                where p.id = e.project_id
                  and wm.user_id = %s::uuid
                  and wm.role in ('owner', 'editor')
              )
            returning
                e.id::text,
                e.project_id::text,
                (
                    select wm.role
                    from projects p
                    join workspace_members wm on wm.workspace_id = p.workspace_id
                    where p.id = e.project_id
                      and wm.user_id = %s::uuid
                    limit 1
                ) as my_role,
                e.hypothesis,
                e.primary_metric,
                e.guardrail_metrics,
                e.status,
                e.created_by::text,
                e.created_at::text,
                e.started_at::text,
                e.ended_at::text
        """

    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (experiment_id, user_id, user_id))
            row = cur.fetchone()
    if not row:
        raise PermissionError("Not allowed to update this experiment")
    return {
        "id": row[0],
        "project_id": row[1],
        "my_role": row[2],
        "hypothesis": row[3],
        "primary_metric": row[4],
        "guardrail_metrics": row[5] or [],
        "status": row[6],
        "created_by": row[7],
        "created_at": row[8],
        "started_at": row[9],
        "ended_at": row[10],
    }


def list_variants_for_user(user_id: str, experiment_id: str) -> list[dict]:
    sql = """
        select
            v.id::text,
            v.experiment_id::text,
            v.variant_key,
            v.config_json,
            v.traffic_weight
        from variants v
        join experiments e on e.id = v.experiment_id
        join projects p on p.id = e.project_id
        join workspace_members wm on wm.workspace_id = p.workspace_id
        where v.experiment_id = %s::uuid
          and wm.user_id = %s::uuid
        order by v.variant_key asc
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (experiment_id, user_id))
            rows = cur.fetchall()
    return [
        {
            "id": row[0],
            "experiment_id": row[1],
            "variant_key": row[2],
            "config_json": row[3] or {},
            "traffic_weight": float(row[4]),
        }
        for row in rows
    ]


def create_variant_for_user(user_id: str, experiment_id: str, body: VariantCreateRequest) -> dict:
    sql = """
        insert into variants (experiment_id, variant_key, config_json, traffic_weight)
        select %s::uuid, %s, %s::jsonb, %s
        where exists (
            select 1
            from experiments e
            join projects p on p.id = e.project_id
            join workspace_members wm on wm.workspace_id = p.workspace_id
            where e.id = %s::uuid
              and wm.user_id = %s::uuid
              and wm.role in ('owner', 'editor')
        )
        on conflict (experiment_id, variant_key) do nothing
        returning
            id::text,
            experiment_id::text,
            variant_key,
            config_json,
            traffic_weight
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    experiment_id,
                    body.variant_key,
                    json.dumps(body.config_json),
                    body.traffic_weight,
                    experiment_id,
                    user_id,
                ),
            )
            row = cur.fetchone()
    if not row:
        raise PermissionError("Not allowed or variant_key already exists")
    return {
        "id": row[0],
        "experiment_id": row[1],
        "variant_key": row[2],
        "config_json": row[3] or {},
        "traffic_weight": float(row[4]),
    }


def update_variant_for_user(
    user_id: str,
    experiment_id: str,
    variant_key: str,
    body: VariantUpdateRequest,
) -> dict:
    fields = []
    params = []
    if body.config_json is not None:
        fields.append("config_json = %s::jsonb")
        params.append(json.dumps(body.config_json))
    if body.traffic_weight is not None:
        fields.append("traffic_weight = %s")
        params.append(body.traffic_weight)
    if not fields:
        raise ValueError("No fields to update")

    sql = f"""
        update variants v
        set {", ".join(fields)}
        from experiments e, projects p, workspace_members wm
        where v.experiment_id = %s::uuid
          and v.variant_key = %s
          and e.id = v.experiment_id
          and p.id = e.project_id
          and wm.workspace_id = p.workspace_id
          and wm.user_id = %s::uuid
          and wm.role in ('owner', 'editor')
        returning
            v.id::text,
            v.experiment_id::text,
            v.variant_key,
            v.config_json,
            v.traffic_weight
    """
    params.extend([experiment_id, variant_key, user_id])

    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            row = cur.fetchone()
    if not row:
        raise PermissionError("Variant not found or not allowed")
    return {
        "id": row[0],
        "experiment_id": row[1],
        "variant_key": row[2],
        "config_json": row[3] or {},
        "traffic_weight": float(row[4]),
    }


def delete_variant_for_user(user_id: str, experiment_id: str, variant_key: str) -> None:
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select count(*)
                from variants v
                where v.experiment_id = %s::uuid
                """,
                (experiment_id,),
            )
            count_row = cur.fetchone()
            variant_count = int(count_row[0] if count_row else 0)
            if variant_count <= 2:
                raise ValueError("At least two variants must remain")

            cur.execute(
                """
                delete from variants v
                using experiments e, projects p, workspace_members wm
                where v.experiment_id = %s::uuid
                  and v.variant_key = %s
                  and e.id = v.experiment_id
                  and p.id = e.project_id
                  and wm.workspace_id = p.workspace_id
                  and wm.user_id = %s::uuid
                  and wm.role in ('owner', 'editor')
                """,
                (experiment_id, variant_key, user_id),
            )
            if cur.rowcount <= 0:
                raise PermissionError("Variant not found or not allowed")
