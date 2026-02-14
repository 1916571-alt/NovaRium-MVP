import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.core.config import settings
from apps.api.db.session import get_db_conn


def _should_run_integration() -> bool:
    return os.getenv("RUN_DB_INTEGRATION") == "1" and bool(settings.database_url)


@pytest.mark.skipif(not _should_run_integration(), reason="DB integration disabled")
def test_rls_workspace_project_isolation():
    user1 = str(uuid.uuid4())
    user2 = str(uuid.uuid4())

    ws1 = None
    ws2 = None
    p1 = None
    p2 = None

    # Ensure required tables exist; skip if migrations are not applied.
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("select 1 from workspaces limit 1")
    except Exception:
        pytest.skip("Required tables not present; apply migrations first")

    try:
        # Seed users.
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "insert into users (id, email) values (%s::uuid, %s) on conflict (id) do nothing",
                    (user1, f"{user1}@local.invalid"),
                )
                cur.execute(
                    "insert into users (id, email) values (%s::uuid, %s) on conflict (id) do nothing",
                    (user2, f"{user2}@local.invalid"),
                )

        # User1 creates own workspace/member/project.
        with get_db_conn(user_id=user1) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into workspaces (owner_user_id, name)
                    values (%s::uuid, 'ws-u1')
                    returning id::text
                    """,
                    (user1,),
                )
                ws1 = cur.fetchone()[0]
                cur.execute(
                    """
                    insert into workspace_members (workspace_id, user_id, role)
                    values (%s::uuid, %s::uuid, 'owner')
                    """,
                    (ws1, user1),
                )
                cur.execute(
                    """
                    insert into projects (workspace_id, name)
                    values (%s::uuid, 'proj-u1')
                    returning id::text
                    """,
                    (ws1,),
                )
                p1 = cur.fetchone()[0]

        # User2 creates own workspace/member/project.
        with get_db_conn(user_id=user2) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into workspaces (owner_user_id, name)
                    values (%s::uuid, 'ws-u2')
                    returning id::text
                    """,
                    (user2,),
                )
                ws2 = cur.fetchone()[0]
                cur.execute(
                    """
                    insert into workspace_members (workspace_id, user_id, role)
                    values (%s::uuid, %s::uuid, 'owner')
                    """,
                    (ws2, user2),
                )
                cur.execute(
                    """
                    insert into projects (workspace_id, name)
                    values (%s::uuid, 'proj-u2')
                    returning id::text
                    """,
                    (ws2,),
                )
                p2 = cur.fetchone()[0]

        # RLS check: user1 should see only p1.
        with get_db_conn(user_id=user1) as conn:
            with conn.cursor() as cur:
                cur.execute("select id::text from projects order by id")
                rows = [r[0] for r in cur.fetchall()]
                assert p1 in rows
                assert p2 not in rows

        # RLS check: user2 should see only p2.
        with get_db_conn(user_id=user2) as conn:
            with conn.cursor() as cur:
                cur.execute("select id::text from projects order by id")
                rows = [r[0] for r in cur.fetchall()]
                assert p2 in rows
                assert p1 not in rows

    finally:
        # Best-effort cleanup by owner context.
        if ws1:
            try:
                with get_db_conn(user_id=user1) as conn:
                    with conn.cursor() as cur:
                        cur.execute("delete from workspaces where id = %s::uuid", (ws1,))
            except Exception:
                pass
        if ws2:
            try:
                with get_db_conn(user_id=user2) as conn:
                    with conn.cursor() as cur:
                        cur.execute("delete from workspaces where id = %s::uuid", (ws2,))
            except Exception:
                pass
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("delete from users where id in (%s::uuid, %s::uuid)", (user1, user2))

