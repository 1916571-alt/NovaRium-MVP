from apps.api.db.session import get_db_conn
from apps.api.schemas.projects import ProjectCreateRequest


def list_projects_for_user(user_id: str) -> list[dict]:
    sql = """
        select
            p.id::text as id,
            p.workspace_id::text as workspace_id,
            p.name,
            wm.role,
            p.created_at::text as created_at
        from projects p
        join workspace_members wm on wm.workspace_id = p.workspace_id
        where wm.user_id = %s::uuid
        order by p.created_at desc
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            rows = cur.fetchall()
    return [
        {
            "id": row[0],
            "workspace_id": row[1],
            "name": row[2],
            "my_role": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]


def create_project_for_user(user_id: str, body: ProjectCreateRequest) -> dict:
    sql = """
        insert into projects (workspace_id, name)
        select %s::uuid, %s
        from workspace_members wm
        where wm.workspace_id = %s::uuid
          and wm.user_id = %s::uuid
          and wm.role in ('owner', 'editor')
        returning
            id::text,
            workspace_id::text,
            name,
            (
                select wm2.role
                from workspace_members wm2
                where wm2.workspace_id = projects.workspace_id
                  and wm2.user_id = %s::uuid
                limit 1
            ) as my_role,
            created_at::text
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (body.workspace_id, body.name, body.workspace_id, user_id, user_id),
            )
            row = cur.fetchone()
    if not row:
        raise PermissionError(
            "Not allowed to create project in this workspace or workspace not found"
        )
    return {
        "id": row[0],
        "workspace_id": row[1],
        "name": row[2],
        "my_role": row[3],
        "created_at": row[4],
    }
