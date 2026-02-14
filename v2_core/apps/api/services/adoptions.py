import json

from apps.api.db.session import get_db_conn
from apps.api.schemas.adoptions import AdoptionCreateRequest


def merge_state(current_state: dict, patch: dict) -> dict:
    result = dict(current_state or {})
    for key, value in (patch or {}).items():
        if (
            isinstance(value, dict)
            and isinstance(result.get(key), dict)
        ):
            result[key] = merge_state(result[key], value)
        else:
            result[key] = value
    return result


def build_adoption_patch(adoption: dict) -> dict:
    experiment_id = adoption["experiment_id"]
    return {
        "features": {
            f"experiment:{experiment_id}": {
                "variant": adoption["winning_variant_key"],
                "traffic_percentage": adoption["traffic_percentage"],
                "adoption_id": adoption["id"],
            }
        }
    }


def _get_project_id_for_experiment(user_id: str, experiment_id: str) -> str | None:
    sql = """
        select e.project_id::text
        from experiments e
        join projects p on p.id = e.project_id
        join workspace_members wm on wm.workspace_id = p.workspace_id
        where e.id = %s::uuid
          and wm.user_id = %s::uuid
          and wm.role in ('owner', 'editor')
        limit 1
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (experiment_id, user_id))
            row = cur.fetchone()
    return row[0] if row else None


def _ensure_user_journey(user_id: str, project_id: str) -> dict:
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into user_journeys (user_id, project_id, start_state_json, current_state_json)
                values (%s::uuid, %s::uuid, '{}'::jsonb, '{}'::jsonb)
                on conflict (user_id, project_id) do nothing
                """,
                (user_id, project_id),
            )
            cur.execute(
                """
                select id::text, current_state_json
                from user_journeys
                where user_id = %s::uuid and project_id = %s::uuid
                limit 1
                """,
                (user_id, project_id),
            )
            row = cur.fetchone()
    return {"journey_id": row[0], "current_state_json": row[1] or {}}


def _apply_patch_to_journey(
    user_id: str,
    journey_id: str,
    current_state: dict,
    patch: dict,
    source_type: str,
    source_id: str,
    event_type: str,
    event_payload: dict,
) -> None:
    merged = merge_state(current_state or {}, patch or {})
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                update user_journeys
                set current_state_json = %s::jsonb,
                    updated_at = now()
                where id = %s::uuid
                """,
                (json.dumps(merged), journey_id),
            )
            cur.execute(
                """
                insert into journey_patches (journey_id, source_type, source_id, patch_json)
                values (%s::uuid, %s, %s, %s::jsonb)
                """,
                (journey_id, source_type, source_id, json.dumps(patch)),
            )
            cur.execute(
                """
                insert into journey_events (journey_id, event_type, payload_json)
                values (%s::uuid, %s, %s::jsonb)
                """,
                (journey_id, event_type, json.dumps(event_payload)),
            )


def create_adoption_for_user(user_id: str, body: AdoptionCreateRequest) -> dict:
    project_id = _get_project_id_for_experiment(user_id, body.experiment_id)
    if not project_id:
        raise PermissionError("Not allowed to adopt this experiment")

    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into adoptions (
                    experiment_id, winning_variant_key, traffic_percentage, reason, adopted_by
                )
                values (%s::uuid, %s, %s, %s, %s::uuid)
                returning id, experiment_id::text, winning_variant_key, traffic_percentage,
                          reason, adopted_by::text, adopted_at::text, rolled_back_at::text
                """,
                (
                    body.experiment_id,
                    body.winning_variant_key,
                    body.traffic_percentage,
                    body.reason,
                    user_id,
                ),
            )
            row = cur.fetchone()

            cur.execute(
                """
                insert into feature_states (project_id, feature_key, state_json)
                values (
                    %s::uuid,
                    %s,
                    %s::jsonb
                )
                on conflict (project_id, feature_key)
                do update set state_json = excluded.state_json, updated_at = now()
                """,
                (
                    project_id,
                    f"experiment:{body.experiment_id}",
                    json.dumps(
                        {
                            "variant": body.winning_variant_key,
                            "traffic_percentage": body.traffic_percentage,
                            "adoption_id": row[0],
                        }
                    ),
                ),
            )

    adoption = {
        "id": row[0],
        "experiment_id": row[1],
        "winning_variant_key": row[2],
        "traffic_percentage": float(row[3]),
        "reason": row[4],
        "adopted_by": row[5],
        "adopted_at": row[6],
        "rolled_back_at": row[7],
    }

    journey = _ensure_user_journey(user_id, project_id)
    patch = build_adoption_patch(adoption)
    _apply_patch_to_journey(
        user_id=user_id,
        journey_id=journey["journey_id"],
        current_state=journey["current_state_json"],
        patch=patch,
        source_type="adoption",
        source_id=str(adoption["id"]),
        event_type="adoption_created",
        event_payload=adoption,
    )
    return adoption


def update_adoption_rollout_for_user(user_id: str, adoption_id: int, traffic_percentage: float) -> dict:
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select a.id, a.experiment_id::text, a.winning_variant_key, a.traffic_percentage,
                       a.reason, a.adopted_by::text, a.adopted_at::text, a.rolled_back_at::text,
                       e.project_id::text
                from adoptions a
                join experiments e on e.id = a.experiment_id
                join projects p on p.id = e.project_id
                join workspace_members wm on wm.workspace_id = p.workspace_id
                where a.id = %s
                  and wm.user_id = %s::uuid
                  and wm.role in ('owner', 'editor')
                limit 1
                """,
                (adoption_id, user_id),
            )
            row = cur.fetchone()
            if not row:
                raise PermissionError("Not allowed to update rollout for this adoption")

            cur.execute(
                """
                update adoptions
                set traffic_percentage = %s
                where id = %s
                returning id, experiment_id::text, winning_variant_key, traffic_percentage,
                          reason, adopted_by::text, adopted_at::text, rolled_back_at::text
                """,
                (traffic_percentage, adoption_id),
            )
            updated = cur.fetchone()

            cur.execute(
                """
                insert into feature_states (project_id, feature_key, state_json)
                values (%s::uuid, %s, %s::jsonb)
                on conflict (project_id, feature_key)
                do update set state_json = excluded.state_json, updated_at = now()
                """,
                (
                    row[8],
                    f"experiment:{row[1]}",
                    json.dumps(
                        {
                            "variant": updated[2],
                            "traffic_percentage": float(updated[3]),
                            "adoption_id": updated[0],
                        }
                    ),
                ),
            )

    adoption = {
        "id": updated[0],
        "experiment_id": updated[1],
        "winning_variant_key": updated[2],
        "traffic_percentage": float(updated[3]),
        "reason": updated[4],
        "adopted_by": updated[5],
        "adopted_at": updated[6],
        "rolled_back_at": updated[7],
    }
    journey = _ensure_user_journey(user_id, row[8])
    patch = build_adoption_patch(adoption)
    _apply_patch_to_journey(
        user_id=user_id,
        journey_id=journey["journey_id"],
        current_state=journey["current_state_json"],
        patch=patch,
        source_type="adoption",
        source_id=str(adoption["id"]),
        event_type="adoption_rollout_updated",
        event_payload={"adoption_id": adoption["id"], "traffic_percentage": adoption["traffic_percentage"]},
    )
    return adoption


def rollback_adoption_for_user(user_id: str, adoption_id: int) -> dict:
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select a.id, a.experiment_id::text, a.winning_variant_key, a.traffic_percentage,
                       a.reason, a.adopted_by::text, a.adopted_at::text, a.rolled_back_at::text,
                       e.project_id::text
                from adoptions a
                join experiments e on e.id = a.experiment_id
                join projects p on p.id = e.project_id
                join workspace_members wm on wm.workspace_id = p.workspace_id
                where a.id = %s
                  and wm.user_id = %s::uuid
                  and wm.role in ('owner', 'editor')
                limit 1
                """,
                (adoption_id, user_id),
            )
            row = cur.fetchone()
            if not row:
                raise PermissionError("Not allowed to rollback this adoption")

            cur.execute(
                """
                update adoptions
                set rolled_back_at = now()
                where id = %s
                returning id, experiment_id::text, winning_variant_key, traffic_percentage,
                          reason, adopted_by::text, adopted_at::text, rolled_back_at::text
                """,
                (adoption_id,),
            )
            updated = cur.fetchone()

            cur.execute(
                """
                insert into feature_states (project_id, feature_key, state_json)
                values (%s::uuid, %s, %s::jsonb)
                on conflict (project_id, feature_key)
                do update set state_json = excluded.state_json, updated_at = now()
                """,
                (
                    row[8],
                    f"experiment:{row[1]}",
                    json.dumps(
                        {
                            "variant": updated[2],
                            "traffic_percentage": 0.0,
                            "adoption_id": updated[0],
                            "rolled_back": True,
                        }
                    ),
                ),
            )

    adoption = {
        "id": updated[0],
        "experiment_id": updated[1],
        "winning_variant_key": updated[2],
        "traffic_percentage": float(updated[3]),
        "reason": updated[4],
        "adopted_by": updated[5],
        "adopted_at": updated[6],
        "rolled_back_at": updated[7],
    }
    journey = _ensure_user_journey(user_id, row[8])
    patch = {
        "features": {
            f"experiment:{adoption['experiment_id']}": {
                "variant": adoption["winning_variant_key"],
                "traffic_percentage": 0.0,
                "adoption_id": adoption["id"],
                "rolled_back": True,
            }
        }
    }
    _apply_patch_to_journey(
        user_id=user_id,
        journey_id=journey["journey_id"],
        current_state=journey["current_state_json"],
        patch=patch,
        source_type="adoption",
        source_id=str(adoption["id"]),
        event_type="adoption_rolled_back",
        event_payload={"adoption_id": adoption["id"]},
    )
    return adoption

