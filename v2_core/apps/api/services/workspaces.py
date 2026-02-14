from apps.api.db.session import get_db_conn
from apps.api.schemas.workspaces import (
    WorkspaceCreateRequest,
    WorkspaceMemberAddRequest,
    WorkspaceRetentionUpdateRequest,
)


def list_workspaces_for_user(user_id: str) -> list[dict]:
    sql = """
        select
            w.id::text,
            w.owner_user_id::text,
            w.name,
            w.simulation_retention_days,
            wm.role,
            w.created_at::text
        from workspaces w
        join workspace_members wm on wm.workspace_id = w.id
        where wm.user_id = %s::uuid
        order by w.created_at desc
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            rows = cur.fetchall()
    return [
        {
            "id": row[0],
            "owner_user_id": row[1],
            "name": row[2],
            "simulation_retention_days": int(row[3]),
            "my_role": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]


def create_workspace_for_user(user_id: str, body: WorkspaceCreateRequest) -> dict:
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into workspaces (owner_user_id, name)
                values (%s::uuid, %s)
                returning id::text, owner_user_id::text, name, simulation_retention_days, created_at::text
                """,
                (user_id, body.name),
            )
            row = cur.fetchone()

            cur.execute(
                """
                insert into workspace_members (workspace_id, user_id, role)
                values (%s::uuid, %s::uuid, 'owner')
                on conflict (workspace_id, user_id) do nothing
                """,
                (row[0], user_id),
            )
    return {
        "id": row[0],
        "owner_user_id": row[1],
        "name": row[2],
        "simulation_retention_days": int(row[3]),
        "my_role": "owner",
        "created_at": row[4],
    }


def add_member_to_workspace_for_user(
    actor_user_id: str, workspace_id: str, body: WorkspaceMemberAddRequest
) -> None:
    with get_db_conn(user_id=actor_user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select 1
                from workspace_members wm
                where wm.workspace_id = %s::uuid
                  and wm.user_id = %s::uuid
                  and wm.role in ('owner', 'editor')
                limit 1
                """,
                (workspace_id, actor_user_id),
            )
            is_allowed = cur.fetchone() is not None
            if not is_allowed:
                raise PermissionError("Only owner/editor can add members")

            cur.execute(
                """
                insert into workspace_members (workspace_id, user_id, role)
                values (%s::uuid, %s::uuid, %s)
                on conflict (workspace_id, user_id)
                do update set role = excluded.role
                """,
                (workspace_id, body.user_id, body.role),
            )


def update_workspace_retention_for_user(
    actor_user_id: str,
    workspace_id: str,
    body: WorkspaceRetentionUpdateRequest,
) -> dict:
    with get_db_conn(user_id=actor_user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select w.simulation_retention_days
                from workspaces w
                join workspace_members wm on wm.workspace_id = w.id
                where w.id = %s::uuid
                  and wm.user_id = %s::uuid
                  and wm.role in ('owner', 'editor')
                limit 1
                """,
                (workspace_id, actor_user_id),
            )
            current_row = cur.fetchone()
            if not current_row:
                raise PermissionError("Not allowed to update workspace retention policy")
            old_retention = int(current_row[0])

            cur.execute(
                """
                update workspaces w
                set simulation_retention_days = %s
                where w.id = %s::uuid
                returning
                    w.id::text,
                    w.owner_user_id::text,
                    w.name,
                    w.simulation_retention_days,
                    (
                        select wm2.role
                        from workspace_members wm2
                        where wm2.workspace_id = w.id
                          and wm2.user_id = %s::uuid
                        limit 1
                    ) as my_role,
                    w.created_at::text
                """,
                (
                    body.simulation_retention_days,
                    workspace_id,
                    actor_user_id,
                ),
            )
            row = cur.fetchone()

            if int(body.simulation_retention_days) != old_retention:
                cur.execute(
                    """
                    insert into workspace_retention_audits (
                        workspace_id, changed_by_user_id, old_retention_days, new_retention_days
                    )
                    values (%s::uuid, %s::uuid, %s, %s)
                    """,
                    (
                        workspace_id,
                        actor_user_id,
                        old_retention,
                        int(body.simulation_retention_days),
                    ),
                )

    if not row:
        raise PermissionError("Not allowed to update workspace retention policy")
    return {
        "id": row[0],
        "owner_user_id": row[1],
        "name": row[2],
        "simulation_retention_days": int(row[3]),
        "my_role": row[4],
        "created_at": row[5],
    }


def list_workspace_retention_audit_for_user(
    actor_user_id: str,
    workspace_id: str,
    changed_by_user_id: str | None = None,
    changed_at_from: str | None = None,
    changed_at_to: str | None = None,
    limit: int = 50,
) -> list[dict]:
    where_parts = [
        "a.workspace_id = %s::uuid",
        "wm.user_id = %s::uuid",
    ]
    params: list = [workspace_id, actor_user_id]
    if changed_by_user_id:
        where_parts.append("a.changed_by_user_id = %s::uuid")
        params.append(changed_by_user_id)
    if changed_at_from:
        where_parts.append("a.changed_at >= %s::timestamptz")
        params.append(changed_at_from)
    if changed_at_to:
        where_parts.append("a.changed_at <= %s::timestamptz")
        params.append(changed_at_to)
    params.append(limit)

    where_sql = " and ".join(where_parts)

    with get_db_conn(user_id=actor_user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                select
                    a.id,
                    a.workspace_id::text,
                    a.changed_by_user_id::text,
                    a.old_retention_days,
                    a.new_retention_days,
                    a.changed_at::text
                from workspace_retention_audits a
                join workspace_members wm on wm.workspace_id = a.workspace_id
                where {where_sql}
                order by a.changed_at desc, a.id desc
                limit %s
                """,
                tuple(params),
            )
            rows = cur.fetchall()
    return [
        {
            "id": int(row[0]),
            "workspace_id": row[1],
            "changed_by_user_id": row[2],
            "old_retention_days": int(row[3]),
            "new_retention_days": int(row[4]),
            "changed_at": row[5],
        }
        for row in rows
    ]
