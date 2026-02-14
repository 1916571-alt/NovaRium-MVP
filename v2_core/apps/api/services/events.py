import json

from psycopg2.extras import execute_values

from apps.api.db.session import get_db_conn
from apps.api.schemas.events import EventIngestBatchRequest


def ingest_events_for_user(user_id: str, body: EventIngestBatchRequest) -> dict:
    items = list(body.items)
    if not items:
        return {
            "accepted_count": 0,
            "duplicated_count": 0,
            "dropped_count": 0,
            "dropped_reasons": [],
        }

    local_dup_count = 0
    deduped_items = []
    seen_keys: set[tuple[str, str]] = set()
    for item in items:
        if item.idempotency_key:
            dedupe_key = (item.project_id, item.idempotency_key)
            if dedupe_key in seen_keys:
                local_dup_count += 1
                continue
            seen_keys.add(dedupe_key)
        deduped_items.append(item)

    project_ids = sorted({item.project_id for item in deduped_items})

    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select p.id::text
                from projects p
                join workspace_members wm on wm.workspace_id = p.workspace_id
                where p.id = any(%s::uuid[])
                  and wm.user_id = %s::uuid
                """,
                (project_ids, user_id),
            )
            allowed_projects = {row[0] for row in cur.fetchall()}

            missing_projects = [pid for pid in project_ids if pid not in allowed_projects]
            if missing_projects:
                raise PermissionError(
                    f"Not allowed to ingest events for project(s): {', '.join(missing_projects)}"
                )

            rows = [
                (
                    item.project_id,
                    item.experiment_id,
                    item.user_key,
                    item.run_id,
                    item.event_name,
                    item.event_time,
                    float(item.value),
                    json.dumps(item.props_json),
                    item.idempotency_key,
                    item.schema_version,
                    item.source,
                )
                for item in deduped_items
            ]

            execute_values(
                cur,
                """
                insert into events (
                    project_id,
                    experiment_id,
                    user_key,
                    run_id,
                    event_name,
                    event_time,
                    value,
                    props_json,
                    idempotency_key,
                    schema_version,
                    source,
                    received_at
                )
                values %s
                on conflict (project_id, idempotency_key) do nothing
                """,
                rows,
                template=(
                    "(%s::uuid, %s::uuid, %s, %s, %s, coalesce(%s::timestamptz, now()), "
                    "%s, %s::jsonb, %s, %s, %s, now())"
                ),
            )
            inserted_count = int(cur.rowcount)

    db_dup_count = len(deduped_items) - inserted_count
    dropped_reasons: list[str] = []
    if local_dup_count > 0:
        dropped_reasons.append(
            f"dropped {local_dup_count} duplicate item(s) by idempotency_key inside request"
        )
    if db_dup_count > 0:
        dropped_reasons.append(
            f"dropped {db_dup_count} duplicate item(s) already ingested previously"
        )

    return {
        "accepted_count": inserted_count,
        "duplicated_count": local_dup_count + db_dup_count,
        "dropped_count": local_dup_count + db_dup_count,
        "dropped_reasons": dropped_reasons,
    }
