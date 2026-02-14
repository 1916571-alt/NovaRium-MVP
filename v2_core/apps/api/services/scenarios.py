import datetime as dt
import hashlib
import hmac
import json
import re
import uuid
from typing import Any

from apps.api.core.config import settings
from apps.api.db.session import get_db_conn

_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
_DIFFICULTY_VALUES = {"easy", "medium", "hard"}
_SUPPORTED_SCHEMA_VERSIONS = {None, "scenario-pack-v1", "scenario-pack-v2"}


def _pick(source: dict, keys: list[str], default=None):
    for k in keys:
        if k in source:
            return source.get(k)
    return default


def adapt_v2_payload_to_v1(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("v2 payload must be an object")

    # v2 may wrap content under `data`, and may use mixed camel/snake keys.
    container = payload.get("data") if isinstance(payload.get("data"), dict) else payload

    experiments_raw = _pick(container, ["experiments"], [])
    challenges_raw = _pick(container, ["sql_challenges", "sqlChallenges"], [])
    feature_states_raw = _pick(container, ["feature_states", "featureStates"], [])
    posts_raw = _pick(container, ["community_posts", "communityPosts"], [])

    if experiments_raw is None:
        experiments_raw = []
    if challenges_raw is None:
        challenges_raw = []
    if feature_states_raw is None:
        feature_states_raw = []
    if posts_raw is None:
        posts_raw = []

    experiments_v1: list[dict] = []
    for exp in experiments_raw:
        if not isinstance(exp, dict):
            continue
        metrics = exp.get("metrics") if isinstance(exp.get("metrics"), dict) else {}
        primary_metric = _pick(exp, ["primary_metric", "primaryMetric"], None)
        if not primary_metric:
            primary_metric = _pick(metrics, ["primary_metric", "primaryMetric", "primary"], None)
        guardrails = _pick(exp, ["guardrail_metrics", "guardrailMetrics"], None)
        if guardrails is None:
            guardrails = _pick(metrics, ["guardrail_metrics", "guardrailMetrics", "guardrails"], [])
        variants_raw = _pick(exp, ["variants"], []) or []
        variants_v1: list[dict] = []
        for variant in variants_raw:
            if not isinstance(variant, dict):
                continue
            variants_v1.append(
                {
                    "variant_key": _pick(variant, ["variant_key", "variantKey", "key"], "variant"),
                    "config_json": _pick(variant, ["config_json", "configJson", "config"], {}),
                    "traffic_weight": _pick(variant, ["traffic_weight", "trafficWeight", "weight"], 0.0),
                }
            )
        experiments_v1.append(
            {
                "source_experiment_id": _pick(exp, ["source_experiment_id", "sourceExperimentId", "id"], ""),
                "hypothesis": _pick(exp, ["hypothesis"], "Imported hypothesis"),
                "primary_metric": primary_metric or "purchase_conversion",
                "guardrail_metrics": guardrails or [],
                "variants": variants_v1,
            }
        )

    challenges_v1: list[dict] = []
    for ch in challenges_raw:
        if not isinstance(ch, dict):
            continue
        challenges_v1.append(
            {
                "title": _pick(ch, ["title"], "Imported SQL Challenge"),
                "prompt_md": _pick(ch, ["prompt_md", "promptMd", "prompt"], ""),
                "difficulty": _pick(ch, ["difficulty"], "easy"),
                "expected_schema": _pick(ch, ["expected_schema", "expectedSchema"], {}),
                "expected_metrics": _pick(ch, ["expected_metrics", "expectedMetrics"], {}),
            }
        )

    feature_states_v1: list[dict] = []
    for fs in feature_states_raw:
        if not isinstance(fs, dict):
            continue
        feature_states_v1.append(
            {
                "feature_key": _pick(fs, ["feature_key", "featureKey", "key"], "imported_feature"),
                "state_json": _pick(fs, ["state_json", "stateJson", "state"], {}),
            }
        )

    posts_v1: list[dict] = []
    for post in posts_raw:
        if not isinstance(post, dict):
            continue
        posts_v1.append(
            {
                "title": _pick(post, ["title"], "Imported Post"),
                "body_md": _pick(post, ["body_md", "bodyMd", "body"], ""),
                "tags": _pick(post, ["tags"], []),
            }
        )

    return {
        "experiments": experiments_v1,
        "sql_challenges": challenges_v1,
        "feature_states": feature_states_v1,
        "community_posts": posts_v1,
    }


def adapt_v1_payload_to_v2(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("v1 payload must be an object")

    experiments_v2: list[dict] = []
    for exp in payload.get("experiments") or []:
        if not isinstance(exp, dict):
            continue
        variants_v2: list[dict] = []
        for variant in exp.get("variants") or []:
            if not isinstance(variant, dict):
                continue
            variants_v2.append(
                {
                    "key": variant.get("variant_key"),
                    "config": variant.get("config_json") or {},
                    "weight": variant.get("traffic_weight"),
                }
            )
        experiments_v2.append(
            {
                "sourceExperimentId": exp.get("source_experiment_id"),
                "hypothesis": exp.get("hypothesis"),
                "metrics": {
                    "primary": exp.get("primary_metric"),
                    "guardrails": exp.get("guardrail_metrics") or [],
                },
                "variants": variants_v2,
            }
        )

    challenges_v2: list[dict] = []
    for ch in payload.get("sql_challenges") or []:
        if not isinstance(ch, dict):
            continue
        challenges_v2.append(
            {
                "title": ch.get("title"),
                "prompt": ch.get("prompt_md"),
                "difficulty": ch.get("difficulty"),
                "expectedSchema": ch.get("expected_schema") or {},
                "expectedMetrics": ch.get("expected_metrics") or {},
            }
        )

    feature_states_v2: list[dict] = []
    for fs in payload.get("feature_states") or []:
        if not isinstance(fs, dict):
            continue
        feature_states_v2.append(
            {
                "key": fs.get("feature_key"),
                "state": fs.get("state_json") or {},
            }
        )

    posts_v2: list[dict] = []
    for post in payload.get("community_posts") or []:
        if not isinstance(post, dict):
            continue
        posts_v2.append(
            {
                "title": post.get("title"),
                "body": post.get("body_md"),
                "tags": post.get("tags") or [],
            }
        )

    return {
        "data": {
            "experiments": experiments_v2,
            "sqlChallenges": challenges_v2,
            "featureStates": feature_states_v2,
            "communityPosts": posts_v2,
        }
    }


def _share_secret() -> str:
    return (
        settings.scenario_share_secret
        or settings.supabase_jwt_secret
        or "novarium-scenario-share-dev-secret"
    )


def _sign_share_id(share_id: str) -> str:
    digest = hmac.new(
        _share_secret().encode("utf-8"),
        share_id.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest[:32]


def _build_share_token(share_id: str) -> str:
    return f"{share_id}.{_sign_share_id(share_id)}"


def _hash_share_token(share_token: str) -> str:
    return hashlib.sha256(share_token.encode("utf-8")).hexdigest()


def _verify_share_token(share_token: str) -> str:
    token = (share_token or "").strip()
    parts = token.split(".")
    if len(parts) != 2:
        raise ValueError("Invalid share token")
    share_id, sig = parts
    try:
        uuid.UUID(share_id)
    except ValueError as exc:
        raise ValueError("Invalid share token") from exc
    expected = _sign_share_id(share_id)
    if not hmac.compare_digest(sig, expected):
        raise ValueError("Invalid share token")
    return share_id


def _safe_str(value: Any, default: str, max_len: int) -> str:
    text = str(value or default).strip()
    if not text:
        text = default
    return text[:max_len]


def _normalize_tags_with_stats(
    tags: Any,
    max_items: int = 10,
    max_len: int = 24,
) -> tuple[list[str], dict[str, int]]:
    stats = {
        "non_list_input": 0,
        "normalized_format": 0,
        "dropped_empty": 0,
        "dropped_duplicate": 0,
        "dropped_overflow": 0,
        "truncated": 0,
    }

    if not isinstance(tags, list):
        stats["non_list_input"] = 1
        return [], stats

    out: list[str] = []
    seen: set[str] = set()
    for raw in tags:
        raw_text = str(raw)
        stripped = raw_text.strip()
        lowered = stripped.lower()
        if raw_text != stripped or stripped != lowered:
            stats["normalized_format"] += 1
        tag = lowered
        if not tag or tag in seen:
            if not tag:
                stats["dropped_empty"] += 1
            else:
                stats["dropped_duplicate"] += 1
            continue
        if len(out) >= max_items:
            stats["dropped_overflow"] += 1
            continue
        seen.add(tag)
        if len(tag) > max_len:
            stats["truncated"] += 1
        out.append(tag[:max_len])
    return out, stats


def _safe_tags(tags: Any, max_items: int = 10, max_len: int = 24) -> list[str]:
    normalized, _ = _normalize_tags_with_stats(tags, max_items=max_items, max_len=max_len)
    return normalized


def normalize_import_payload(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")

    experiments_raw = payload.get("experiments")
    sql_challenges_raw = payload.get("sql_challenges")
    feature_states_raw = payload.get("feature_states")
    community_posts_raw = payload.get("community_posts")

    if experiments_raw is None:
        experiments_raw = []
    if sql_challenges_raw is None:
        sql_challenges_raw = []
    if feature_states_raw is None:
        feature_states_raw = []
    if community_posts_raw is None:
        community_posts_raw = []

    if not isinstance(experiments_raw, list):
        raise ValueError("payload.experiments must be a list")
    if not isinstance(sql_challenges_raw, list):
        raise ValueError("payload.sql_challenges must be a list")
    if not isinstance(feature_states_raw, list):
        raise ValueError("payload.feature_states must be a list")
    if not isinstance(community_posts_raw, list):
        raise ValueError("payload.community_posts must be a list")

    if len(experiments_raw) > 200:
        raise ValueError("payload.experiments exceeds max size (200)")
    if len(sql_challenges_raw) > 300:
        raise ValueError("payload.sql_challenges exceeds max size (300)")
    if len(feature_states_raw) > 500:
        raise ValueError("payload.feature_states exceeds max size (500)")
    if len(community_posts_raw) > 500:
        raise ValueError("payload.community_posts exceeds max size (500)")

    experiments: list[dict] = []
    for exp in experiments_raw:
        if not isinstance(exp, dict):
            raise ValueError("payload.experiments contains non-object item")
        variants_raw = exp.get("variants") or []
        if not isinstance(variants_raw, list):
            raise ValueError("experiment.variants must be a list")
        if len(variants_raw) > 20:
            raise ValueError("experiment.variants exceeds max size (20)")

        variants: list[dict] = []
        for variant in variants_raw:
            if not isinstance(variant, dict):
                raise ValueError("experiment.variants contains non-object item")
            variant_key = _safe_str(variant.get("variant_key"), "variant", 64)
            if not _KEY_PATTERN.match(variant_key):
                variant_key = "variant"
            weight = float(variant.get("traffic_weight") or 0.0)
            weight = min(100.0, max(0.0, weight))
            config_json = variant.get("config_json")
            if not isinstance(config_json, dict):
                config_json = {}
            variants.append(
                {
                    "variant_key": variant_key,
                    "config_json": config_json,
                    "traffic_weight": weight,
                }
            )

        guardrails = exp.get("guardrail_metrics")
        if not isinstance(guardrails, list):
            guardrails = []

        experiments.append(
            {
                "source_experiment_id": str(exp.get("source_experiment_id") or ""),
                "hypothesis": _safe_str(exp.get("hypothesis"), "Imported hypothesis", 4000),
                "primary_metric": _safe_str(exp.get("primary_metric"), "purchase_conversion", 120),
                "guardrail_metrics": [str(x)[:120] for x in guardrails[:10]],
                "variants": variants,
            }
        )

    sql_challenges: list[dict] = []
    for ch in sql_challenges_raw:
        if not isinstance(ch, dict):
            raise ValueError("payload.sql_challenges contains non-object item")
        difficulty = _safe_str(ch.get("difficulty"), "easy", 16).lower()
        if difficulty not in _DIFFICULTY_VALUES:
            difficulty = "easy"
        expected_schema = ch.get("expected_schema")
        expected_metrics = ch.get("expected_metrics")
        if not isinstance(expected_schema, dict):
            expected_schema = {}
        if not isinstance(expected_metrics, dict):
            expected_metrics = {}
        sql_challenges.append(
            {
                "title": _safe_str(ch.get("title"), "Imported SQL Challenge", 180),
                "prompt_md": _safe_str(ch.get("prompt_md"), "", 12000),
                "difficulty": difficulty,
                "expected_schema": expected_schema,
                "expected_metrics": expected_metrics,
            }
        )

    feature_states: list[dict] = []
    for fs in feature_states_raw:
        if not isinstance(fs, dict):
            raise ValueError("payload.feature_states contains non-object item")
        feature_key = _safe_str(fs.get("feature_key"), "imported_feature", 120)
        if not _KEY_PATTERN.match(feature_key):
            feature_key = "imported_feature"
        state_json = fs.get("state_json")
        if not isinstance(state_json, dict):
            state_json = {}
        feature_states.append({"feature_key": feature_key, "state_json": state_json})

    community_posts: list[dict] = []
    for post in community_posts_raw:
        if not isinstance(post, dict):
            raise ValueError("payload.community_posts contains non-object item")
        community_posts.append(
            {
                "title": _safe_str(post.get("title"), "Imported Post", 180),
                "body_md": _safe_str(post.get("body_md"), "", 20000),
                "tags": _safe_tags(post.get("tags")),
            }
        )

    return {
        "experiments": experiments,
        "sql_challenges": sql_challenges,
        "feature_states": feature_states,
        "community_posts": community_posts,
    }


def normalize_import_payload_by_version(schema_version: str | None, payload: dict) -> dict:
    if schema_version not in _SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(f"Unsupported scenario schema_version: {schema_version}")
    if schema_version == "scenario-pack-v2":
        return normalize_import_payload(adapt_v2_payload_to_v1(payload))
    return normalize_import_payload(payload)


def _collect_normalization_warnings(schema_version: str | None, payload: dict) -> list[str]:
    source_payload = payload
    if schema_version == "scenario-pack-v2":
        source_payload = adapt_v2_payload_to_v1(payload)

    if not isinstance(source_payload, dict):
        return []

    counters: dict[str, int] = {}

    def add_warning(msg: str):
        counters[msg] = counters.get(msg, 0) + 1

    def add_warning_count(msg: str, count: int):
        if count > 0:
            counters[msg] = counters.get(msg, 0) + count

    experiments = source_payload.get("experiments")
    if isinstance(experiments, list):
        for exp in experiments:
            if not isinstance(exp, dict):
                continue
            if len(str(exp.get("hypothesis") or "")) > 4000:
                add_warning("experiments.hypothesis is truncated to 4000 chars")
            if len(str(exp.get("primary_metric") or "")) > 120:
                add_warning("experiments.primary_metric is truncated to 120 chars")

            variants = exp.get("variants")
            if isinstance(variants, list):
                for variant in variants:
                    if not isinstance(variant, dict):
                        continue
                    key = str(variant.get("variant_key") or "")
                    if key and not _KEY_PATTERN.match(key):
                        add_warning("variants.variant_key invalid format replaced with default")
                    try:
                        weight = float(variant.get("traffic_weight") or 0.0)
                    except (TypeError, ValueError):
                        weight = 0.0
                    if weight < 0.0 or weight > 100.0:
                        add_warning("variants.traffic_weight is clamped to 0..100")

    challenges = source_payload.get("sql_challenges")
    if isinstance(challenges, list):
        for ch in challenges:
            if not isinstance(ch, dict):
                continue
            if len(str(ch.get("title") or "")) > 180:
                add_warning("sql_challenges.title is truncated to 180 chars")
            if len(str(ch.get("prompt_md") or "")) > 12000:
                add_warning("sql_challenges.prompt_md is truncated to 12000 chars")

    feature_states = source_payload.get("feature_states")
    if isinstance(feature_states, list):
        for fs in feature_states:
            if not isinstance(fs, dict):
                continue
            feature_key = str(fs.get("feature_key") or "")
            if feature_key and not _KEY_PATTERN.match(feature_key):
                add_warning("feature_states.feature_key invalid format replaced with default")
            if len(feature_key) > 120:
                add_warning("feature_states.feature_key is truncated to 120 chars")

    posts = source_payload.get("community_posts")
    if isinstance(posts, list):
        for post in posts:
            if not isinstance(post, dict):
                continue
            if len(str(post.get("title") or "")) > 180:
                add_warning("community_posts.title is truncated to 180 chars")
            if len(str(post.get("body_md") or "")) > 20000:
                add_warning("community_posts.body_md is truncated to 20000 chars")
            tags = post.get("tags")
            _, tag_stats = _normalize_tags_with_stats(tags)
            if tags is not None and not isinstance(tags, list):
                add_warning("community_posts.tags non-list replaced with empty list")
            add_warning_count(
                "community_posts.tags normalized by trim/lowercase",
                tag_stats["normalized_format"],
            )
            add_warning_count(
                "community_posts.tags empty items are dropped",
                tag_stats["dropped_empty"],
            )
            add_warning_count(
                "community_posts.tags duplicates are dropped",
                tag_stats["dropped_duplicate"],
            )
            add_warning_count(
                "community_posts.tags overflow items are dropped (max 10)",
                tag_stats["dropped_overflow"],
            )
            add_warning_count(
                "community_posts.tags items are truncated to 24 chars",
                tag_stats["truncated"],
            )

    warnings: list[str] = []
    for msg in sorted(counters.keys()):
        count = counters[msg]
        warnings.append(f"{msg} ({count})" if count > 1 else msg)
    return warnings


def validate_scenario_pack_payload(schema_version: str | None, payload: dict) -> dict:
    normalized = normalize_import_payload_by_version(schema_version, payload)
    experiments = normalized["experiments"]
    variant_count = 0
    for exp in experiments:
        variants = exp.get("variants") or []
        variant_count += len(variants)

    accepted_version = schema_version or "scenario-pack-v1"
    return {
        "accepted_schema_version": accepted_version,
        "normalized_counts": {
            "experiments": len(experiments),
            "variants": variant_count,
            "sql_challenges": len(normalized["sql_challenges"]),
            "feature_states": len(normalized["feature_states"]),
            "community_posts": len(normalized["community_posts"]),
        },
        "warnings": _collect_normalization_warnings(schema_version, payload),
    }


def export_scenario_pack_for_user(
    user_id: str,
    project_id: str,
    schema_version: str | None = None,
) -> dict:
    if schema_version not in _SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(f"Unsupported scenario schema_version: {schema_version}")
    resolved_version = schema_version or "scenario-pack-v1"

    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select p.id::text, p.name
                from projects p
                join workspace_members wm on wm.workspace_id = p.workspace_id
                where p.id = %s::uuid
                  and wm.user_id = %s::uuid
                limit 1
                """,
                (project_id, user_id),
            )
            project_row = cur.fetchone()
            if not project_row:
                raise PermissionError("Project not accessible")

            cur.execute(
                """
                select
                    e.id::text,
                    e.hypothesis,
                    e.primary_metric,
                    e.guardrail_metrics,
                    e.status
                from experiments e
                where e.project_id = %s::uuid
                order by e.created_at asc
                """,
                (project_id,),
            )
            experiments = cur.fetchall()

            cur.execute(
                """
                select
                    v.experiment_id::text,
                    v.variant_key,
                    v.config_json,
                    v.traffic_weight
                from variants v
                join experiments e on e.id = v.experiment_id
                where e.project_id = %s::uuid
                order by v.experiment_id, v.variant_key
                """,
                (project_id,),
            )
            variants = cur.fetchall()

            cur.execute(
                """
                select
                    c.title,
                    c.prompt_md,
                    c.difficulty,
                    c.expected_schema,
                    c.expected_metrics
                from sql_challenges c
                where c.project_id = %s::uuid
                order by c.created_at asc
                """,
                (project_id,),
            )
            challenges = cur.fetchall()

            cur.execute(
                """
                select
                    fs.feature_key,
                    fs.state_json
                from feature_states fs
                where fs.project_id = %s::uuid
                order by fs.feature_key asc
                """,
                (project_id,),
            )
            feature_states = cur.fetchall()

            cur.execute(
                """
                select
                    cp.title,
                    cp.body_md,
                    cp.tags
                from community_posts cp
                where cp.project_id = %s::uuid
                order by cp.created_at asc
                """,
                (project_id,),
            )
            posts = cur.fetchall()

    exp_by_id: dict[str, dict[str, Any]] = {}
    for row in experiments:
        exp_by_id[row[0]] = {
            "source_experiment_id": row[0],
            "hypothesis": row[1],
            "primary_metric": row[2],
            "guardrail_metrics": row[3] or [],
            "status": row[4],
            "variants": [],
        }

    for v in variants:
        exp_id = v[0]
        if exp_id not in exp_by_id:
            continue
        exp_by_id[exp_id]["variants"].append(
            {
                "variant_key": v[1],
                "config_json": v[2] or {},
                "traffic_weight": float(v[3]),
            }
        )

    payload = {
        "project": {
            "source_project_id": project_row[0],
            "source_project_name": project_row[1],
        },
        "experiments": list(exp_by_id.values()),
        "sql_challenges": [
            {
                "title": row[0],
                "prompt_md": row[1],
                "difficulty": row[2],
                "expected_schema": row[3] or {},
                "expected_metrics": row[4] or {},
            }
            for row in challenges
        ],
        "feature_states": [
            {
                "feature_key": row[0],
                "state_json": row[1] or {},
            }
            for row in feature_states
        ],
        "community_posts": [
            {
                "title": row[0],
                "body_md": row[1],
                "tags": row[2] or [],
            }
            for row in posts
        ],
    }

    out_payload = payload
    if resolved_version == "scenario-pack-v2":
        out_payload = adapt_v1_payload_to_v2(payload)

    return {
        "schema_version": resolved_version,
        "exported_at": dt.datetime.utcnow().isoformat(),
        "source_project_id": project_row[0],
        "source_project_name": project_row[1],
        "payload": out_payload,
    }


def import_scenario_pack_for_user(
    user_id: str,
    workspace_id: str,
    project_name: str,
    schema_version: str | None,
    payload: dict,
) -> dict:
    normalized = normalize_import_payload_by_version(schema_version, payload)
    experiments = normalized["experiments"]
    sql_challenges = normalized["sql_challenges"]
    feature_states = normalized["feature_states"]
    community_posts = normalized["community_posts"]

    imported_experiments = 0
    imported_variants = 0
    imported_sql_challenges = 0
    imported_feature_states = 0
    imported_posts = 0

    with get_db_conn(user_id=user_id) as conn:
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
                (workspace_id, user_id),
            )
            if not cur.fetchone():
                raise PermissionError("Not allowed to import into this workspace")

            cur.execute(
                """
                insert into projects (workspace_id, name)
                values (%s::uuid, %s)
                returning id::text
                """,
                (workspace_id, project_name),
            )
            project_id = cur.fetchone()[0]

            for exp in experiments:
                cur.execute(
                    """
                    insert into experiments (
                        project_id, hypothesis, primary_metric, guardrail_metrics, status, created_by
                    )
                    values (%s::uuid, %s, %s, %s::jsonb, 'draft', %s::uuid)
                    returning id::text
                    """,
                    (
                        project_id,
                        str(exp.get("hypothesis") or "Imported hypothesis"),
                        str(exp.get("primary_metric") or "purchase_conversion"),
                        json.dumps(exp.get("guardrail_metrics") or []),
                        user_id,
                    ),
                )
                new_exp_id = cur.fetchone()[0]
                imported_experiments += 1

                variants = exp.get("variants") or []
                for variant in variants:
                    cur.execute(
                        """
                        insert into variants (experiment_id, variant_key, config_json, traffic_weight)
                        values (%s::uuid, %s, %s::jsonb, %s)
                        on conflict (experiment_id, variant_key) do nothing
                        """,
                        (
                            new_exp_id,
                            str(variant.get("variant_key") or "variant"),
                            json.dumps(variant.get("config_json") or {}),
                            float(variant.get("traffic_weight") or 0.0),
                        ),
                    )
                    imported_variants += int(cur.rowcount or 0)

            for ch in sql_challenges:
                cur.execute(
                    """
                    insert into sql_challenges (
                        project_id, title, prompt_md, difficulty, expected_schema, expected_metrics
                    )
                    values (%s::uuid, %s, %s, %s, %s::jsonb, %s::jsonb)
                    """,
                    (
                        project_id,
                        str(ch.get("title") or "Imported SQL Challenge"),
                        str(ch.get("prompt_md") or ""),
                        str(ch.get("difficulty") or "easy"),
                        json.dumps(ch.get("expected_schema") or {}),
                        json.dumps(ch.get("expected_metrics") or {}),
                    ),
                )
                imported_sql_challenges += int(cur.rowcount or 0)

            for fs in feature_states:
                cur.execute(
                    """
                    insert into feature_states (project_id, feature_key, state_json)
                    values (%s::uuid, %s, %s::jsonb)
                    on conflict (project_id, feature_key)
                    do update set state_json = excluded.state_json, updated_at = now()
                    """,
                    (
                        project_id,
                        str(fs.get("feature_key") or "imported_feature"),
                        json.dumps(fs.get("state_json") or {}),
                    ),
                )
                imported_feature_states += 1

            for post in community_posts:
                cur.execute(
                    """
                    insert into community_posts (project_id, experiment_id, author_user_id, title, body_md, tags)
                    values (%s::uuid, null, %s::uuid, %s, %s, %s::text[])
                    """,
                    (
                        project_id,
                        user_id,
                        str(post.get("title") or "Imported Post"),
                        str(post.get("body_md") or ""),
                        list(post.get("tags") or []),
                    ),
                )
                imported_posts += int(cur.rowcount or 0)

    return {
        "project_id": project_id,
        "project_name": project_name,
        "imported_experiments": imported_experiments,
        "imported_variants": imported_variants,
        "imported_sql_challenges": imported_sql_challenges,
        "imported_feature_states": imported_feature_states,
        "imported_community_posts": imported_posts,
    }


def create_scenario_share_for_user(
    user_id: str,
    project_id: str,
    schema_version: str | None,
    expires_hours: int,
) -> dict:
    if expires_hours < 1 or expires_hours > 24 * 30:
        raise ValueError("expires_hours must be between 1 and 720")

    export_row = export_scenario_pack_for_user(
        user_id=user_id,
        project_id=project_id,
        schema_version=schema_version,
    )
    share_id = str(uuid.uuid4())
    share_token = _build_share_token(share_id)
    token_hash = _hash_share_token(share_token)
    expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=expires_hours)

    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into scenario_share_links (
                    id, token_hash, created_by_user_id, source_project_id, source_project_name,
                    schema_version, payload_json, expires_at
                )
                values (
                    %s::uuid, %s, %s::uuid, %s::uuid, %s, %s, %s::jsonb, %s::timestamptz
                )
                """,
                (
                    share_id,
                    token_hash,
                    user_id,
                    export_row["source_project_id"],
                    export_row["source_project_name"],
                    export_row["schema_version"],
                    json.dumps(export_row["payload"]),
                    expires_at.isoformat(),
                ),
            )

    return {
        "share_token": share_token,
        "expires_at": expires_at.isoformat(),
        "schema_version": export_row["schema_version"],
    }


def revoke_scenario_share_for_user(user_id: str, share_token: str) -> dict:
    share_id = _verify_share_token(share_token)
    token_hash = _hash_share_token(share_token)

    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                update scenario_share_links
                set revoked_at = now(), revoked_by_user_id = %s::uuid
                where id = %s::uuid
                  and token_hash = %s
                  and created_by_user_id = %s::uuid
                  and revoked_at is null
                returning revoked_at::text
                """,
                (user_id, share_id, token_hash, user_id),
            )
            row = cur.fetchone()
            if not row:
                cur.execute(
                    """
                    select 1
                    from scenario_share_links
                    where id = %s::uuid
                      and token_hash = %s
                    limit 1
                    """,
                    (share_id, token_hash),
                )
                exists_row = cur.fetchone()
                if exists_row:
                    raise PermissionError("Not allowed to revoke this share link")
                raise ValueError("Share link not found or already revoked")

    return {"revoked": True, "revoked_at": str(row[0])}


def resolve_scenario_share(share_token: str) -> dict:
    share_id = _verify_share_token(share_token)
    token_hash = _hash_share_token(share_token)

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select
                    s.schema_version,
                    s.source_project_id::text,
                    s.source_project_name,
                    s.payload_json,
                    s.created_at::text,
                    s.expires_at,
                    s.revoked_at
                from scenario_share_links s
                where s.id = %s::uuid
                  and s.token_hash = %s
                limit 1
                """,
                (share_id, token_hash),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Share link not found")

            now_utc = dt.datetime.now(dt.timezone.utc)
            if row[5] is not None and row[5] < now_utc:
                raise ValueError("Share link expired")
            if row[6] is not None:
                raise ValueError("Share link revoked")

            cur.execute(
                """
                update scenario_share_links
                set last_accessed_at = now()
                where id = %s::uuid
                """,
                (share_id,),
            )

    return {
        "schema_version": str(row[0]),
        "exported_at": str(row[4]),
        "source_project_id": str(row[1]),
        "source_project_name": str(row[2]),
        "payload": row[3] or {},
    }
