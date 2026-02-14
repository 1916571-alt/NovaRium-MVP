from apps.api.db.session import get_db_conn


def get_my_journey_for_project(user_id: str, project_id: str) -> dict | None:
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select
                    j.id::text,
                    j.user_id::text,
                    j.project_id::text,
                    j.start_state_json,
                    j.current_state_json,
                    j.updated_at::text
                from user_journeys j
                where j.user_id = %s::uuid
                  and j.project_id = %s::uuid
                limit 1
                """,
                (user_id, project_id),
            )
            row = cur.fetchone()
            if not row:
                return None

            journey_id = row[0]

            cur.execute(
                """
                select id, source_type, source_id, patch_json, created_at::text
                from journey_patches
                where journey_id = %s::uuid
                order by id desc
                limit 50
                """,
                (journey_id,),
            )
            patch_rows = cur.fetchall()

            cur.execute(
                """
                select id, event_type, payload_json, created_at::text
                from journey_events
                where journey_id = %s::uuid
                order by id desc
                limit 50
                """,
                (journey_id,),
            )
            event_rows = cur.fetchall()

    return {
        "journey_id": row[0],
        "user_id": row[1],
        "project_id": row[2],
        "start_state_json": row[3] or {},
        "current_state_json": row[4] or {},
        "updated_at": row[5],
        "patches": [
            {
                "id": p[0],
                "source_type": p[1],
                "source_id": p[2],
                "patch_json": p[3] or {},
                "created_at": p[4],
            }
            for p in patch_rows
        ],
        "events": [
            {
                "id": e[0],
                "event_type": e[1],
                "payload_json": e[2] or {},
                "created_at": e[3],
            }
            for e in event_rows
        ],
    }

