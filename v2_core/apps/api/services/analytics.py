import datetime as dt
import json
import random

from psycopg2.extras import execute_values

from apps.api.db.session import get_db_conn
from apps.api.schemas.analytics import SimulationBootstrapRequest


FUNNEL_STEPS = [
    "session_start",
    "view_home",
    "view_detail",
    "click_cta",
    "add_to_cart",
    "start_checkout",
    "purchase",
]

TEMPLATE_STEP_PLANS = {
    "commerce": [
        "session_start",
        "view_home",
        "view_detail",
        "click_cta",
        "add_to_cart",
        "start_checkout",
        "purchase",
    ],
    "content": [
        "session_start",
        "view_home",
        "view_detail",
        "click_cta",
        "purchase",
    ],
    "saas": [
        "session_start",
        "view_home",
        "view_detail",
        "click_cta",
        "start_checkout",
        "purchase",
    ],
}

SIMULATION_TEMPLATES = {
    "commerce": {
        "label": "Commerce Funnel",
        "description": "Home -> detail -> cart -> checkout -> purchase conversion optimization",
        "default_user_count": 2400,
        "control_purchase_rate": 0.22,
        "test_purchase_rate": 0.27,
        "hypothesis": "Improved CTA and checkout flow will increase purchase conversion",
        "primary_metric": "purchase_conversion",
        "guardrail_metrics": ["bounce_rate", "avg_order_value"],
    },
    "content": {
        "label": "Content Funnel",
        "description": "Home -> detail -> CTA click -> subscription-style conversion learning",
        "default_user_count": 3000,
        "control_purchase_rate": 0.10,
        "test_purchase_rate": 0.135,
        "hypothesis": "Personalized feed layout will increase content subscription conversion",
        "primary_metric": "cta_click_rate",
        "guardrail_metrics": ["bounce_rate", "session_depth"],
    },
    "saas": {
        "label": "SaaS Funnel",
        "description": "Landing -> detail -> CTA -> checkout style trial/upgrade conversion",
        "default_user_count": 1800,
        "control_purchase_rate": 0.14,
        "test_purchase_rate": 0.18,
        "hypothesis": "Pricing card redesign will increase free-to-paid conversion",
        "primary_metric": "purchase_conversion",
        "guardrail_metrics": ["bounce_rate", "trial_activation_rate"],
    },
}

TEMPLATE_SQL_CHALLENGES = {
    "commerce": [
        {
            "title": "Commerce Funnel Step Conversion",
            "prompt_md": "Compute users by funnel step for a given run_id.",
            "difficulty": "easy",
            "expected_schema": {"columns": ["event_name", "users"]},
            "expected_metrics": {"must_have_columns": ["event_name", "users"], "min_row_count": 3},
            "starter_sql": (
                "select event_name, count(distinct user_key) as users "
                "from events where project_id = :project_id and run_id = :run_id "
                "group by event_name order by users desc"
            ),
        },
        {
            "title": "Commerce Variant Purchase Rate",
            "prompt_md": "Compare purchase conversion rate by variant for a run.",
            "difficulty": "medium",
            "expected_schema": {"columns": ["variant_key", "users", "purchasers", "purchase_rate"]},
            "expected_metrics": {"must_have_columns": ["variant_key", "purchase_rate"], "min_row_count": 2},
            "starter_sql": (
                "select a.variant_key, count(distinct a.user_key) as users, "
                "count(distinct case when e.event_name='purchase' then a.user_key end) as purchasers, "
                "count(distinct case when e.event_name='purchase' then a.user_key end)::float "
                "/ nullif(count(distinct a.user_key),0) as purchase_rate "
                "from assignments a left join events e on e.experiment_id=a.experiment_id "
                "and e.user_key=a.user_key and coalesce(e.run_id,'')=coalesce(a.run_id,'') "
                "where a.experiment_id = :experiment_id and a.run_id = :run_id "
                "group by a.variant_key order by a.variant_key"
            ),
        },
    ],
    "content": [
        {
            "title": "Content CTA Conversion by Step",
            "prompt_md": "Measure CTA clicks from detail viewers.",
            "difficulty": "easy",
            "expected_schema": {"columns": ["detail_viewers", "cta_clickers", "ctr"]},
            "expected_metrics": {"must_have_columns": ["ctr"], "row_count": 1},
            "starter_sql": (
                "with detail as (select distinct user_key from events "
                "where project_id=:project_id and run_id=:run_id and event_name='view_detail'), "
                "cta as (select distinct user_key from events "
                "where project_id=:project_id and run_id=:run_id and event_name='click_cta') "
                "select (select count(*) from detail) as detail_viewers, "
                "(select count(*) from cta) as cta_clickers, "
                "(select count(*) from cta)::float / nullif((select count(*) from detail),0) as ctr"
            ),
        },
        {
            "title": "Content Template Bottleneck Candidate",
            "prompt_md": "Find biggest drop between consecutive content funnel steps.",
            "difficulty": "hard",
            "expected_schema": {"columns": ["from_step", "to_step", "from_users", "to_users", "drop_rate"]},
            "expected_metrics": {"must_have_columns": ["drop_rate"], "min_row_count": 1},
            "starter_sql": (
                "with s as (select event_name, count(distinct user_key) as users "
                "from events where project_id=:project_id and run_id=:run_id "
                "and event_name in ('session_start','view_home','view_detail','click_cta','purchase') "
                "group by event_name) "
                "select 'session_start' as from_step, 'view_home' as to_step, 0 as from_users, 0 as to_users, 0.0 as drop_rate"
            ),
        },
    ],
    "saas": [
        {
            "title": "SaaS Checkout Entry Rate",
            "prompt_md": "Compute start_checkout rate from CTA clickers.",
            "difficulty": "medium",
            "expected_schema": {"columns": ["cta_users", "checkout_users", "checkout_rate"]},
            "expected_metrics": {"must_have_columns": ["checkout_rate"], "row_count": 1},
            "starter_sql": (
                "with c as (select distinct user_key from events "
                "where project_id=:project_id and run_id=:run_id and event_name='click_cta'), "
                "k as (select distinct user_key from events "
                "where project_id=:project_id and run_id=:run_id and event_name='start_checkout') "
                "select (select count(*) from c) as cta_users, "
                "(select count(*) from k) as checkout_users, "
                "(select count(*) from k)::float / nullif((select count(*) from c),0) as checkout_rate"
            ),
        },
        {
            "title": "SaaS Variant Lift Snapshot",
            "prompt_md": "Compute conversion rate per variant and absolute lift.",
            "difficulty": "hard",
            "expected_schema": {"columns": ["variant_key", "purchase_rate"]},
            "expected_metrics": {"must_have_columns": ["variant_key", "purchase_rate"], "min_row_count": 2},
            "starter_sql": (
                "select a.variant_key, "
                "count(distinct case when e.event_name='purchase' then a.user_key end)::float "
                "/ nullif(count(distinct a.user_key),0) as purchase_rate "
                "from assignments a left join events e on e.experiment_id=a.experiment_id "
                "and e.user_key=a.user_key and coalesce(e.run_id,'')=coalesce(a.run_id,'') "
                "where a.experiment_id=:experiment_id and a.run_id=:run_id "
                "group by a.variant_key order by a.variant_key"
            ),
        },
    ],
}

SEED_PRESETS = {"beginner", "standard", "advanced"}


def _preset_defaults_from_template(template: dict, preset: str) -> dict:
    if preset not in SEED_PRESETS:
        raise ValueError(f"Unknown seed preset: {preset}")
    base_users = int(template["default_user_count"])
    base_control = float(template["control_purchase_rate"])
    base_test = float(template["test_purchase_rate"])
    base_delta = max(0.01, base_test - base_control)

    if preset == "beginner":
        users = max(600, int(round(base_users * 0.55)))
        control = max(0.01, min(0.8, base_control * 0.95))
        test = max(control + 0.02, min(0.9, control + base_delta * 1.8))
    elif preset == "advanced":
        users = min(20000, int(round(base_users * 1.9)))
        control = max(0.01, min(0.8, base_control))
        test = max(control + 0.01, min(0.9, control + base_delta * 0.65))
    else:
        users = base_users
        control = base_control
        test = base_test

    return {
        "user_count": int(users),
        "control_purchase_rate": float(control),
        "test_purchase_rate": float(test),
    }


def resolve_template_seed_preset(template_key: str, preset: str) -> dict:
    template = resolve_template_settings(template_key)
    return _preset_defaults_from_template(template, preset)


def list_simulation_templates() -> list[dict]:
    return [
        {
            "key": key,
            "label": value["label"],
            "description": value["description"],
            "default_user_count": int(value["default_user_count"]),
            "default_control_purchase_rate": float(value["control_purchase_rate"]),
            "default_test_purchase_rate": float(value["test_purchase_rate"]),
            "preset_defaults": {
                "beginner": _preset_defaults_from_template(value, "beginner"),
                "standard": _preset_defaults_from_template(value, "standard"),
                "advanced": _preset_defaults_from_template(value, "advanced"),
            },
        }
        for key, value in SIMULATION_TEMPLATES.items()
    ]


def resolve_template_settings(template: str) -> dict:
    if template not in SIMULATION_TEMPLATES:
        raise ValueError(f"Unknown template: {template}")
    return SIMULATION_TEMPLATES[template]


def resolve_template_steps(template: str) -> list[str]:
    if template not in TEMPLATE_STEP_PLANS:
        raise ValueError(f"Unknown template: {template}")
    return list(TEMPLATE_STEP_PLANS[template])


def resolve_template_sql_challenges(template: str) -> list[dict]:
    if template not in TEMPLATE_SQL_CHALLENGES:
        raise ValueError(f"Unknown template: {template}")
    return list(TEMPLATE_SQL_CHALLENGES[template])


def _build_conditional_probs(step_plan: list[str], purchase_rate: float) -> dict[str, float]:
    # Configure intermediate step probabilities and solve purchase probability
    # to approximate final conversion target for each template step plan.
    base_prob = {
        "view_home": 1.0,
        "view_detail": 0.76,
        "click_cta": 0.62,
        "add_to_cart": 0.78,
        "start_checkout": 0.74,
    }
    probs: dict[str, float] = {}
    product = 1.0
    for step in step_plan[1:]:
        if step == "purchase":
            continue
        p = float(base_prob.get(step, 0.70))
        probs[step] = p
        product *= p
    probs["purchase"] = min(0.95, max(0.05, purchase_rate / max(product, 1e-9)))
    return probs


def _simulate_user_events(
    rng: random.Random,
    step_plan: list[str],
    probs: dict[str, float],
) -> list[str]:
    events: list[str] = []
    if step_plan:
        events.append(step_plan[0])
    if len(step_plan) >= 2:
        events.append(step_plan[1])
    for step in step_plan[2:]:
        if rng.random() <= probs[step]:
            events.append(step)
        else:
            events.append("bounce")
            break
    return events


def compute_funnel_overview(step_counts: list[tuple[int, str, int]]) -> dict:
    if not step_counts:
        return {
            "total_users": 0,
            "bottleneck_step": None,
            "steps": [],
        }

    total_users = int(step_counts[0][2])
    steps: list[dict] = []
    prev = None
    worst_dropoff = -1.0
    bottleneck_step = None

    for step_index, step_name, users_count in step_counts:
        users = int(users_count)
        if step_index == 0:
            conversion_rate = 1.0 if total_users > 0 else 0.0
            dropoff_rate = 0.0
        else:
            conversion_rate = (users / total_users) if total_users > 0 else 0.0
            if prev and prev > 0:
                dropoff_rate = max(0.0, min(1.0, (prev - users) / prev))
            else:
                dropoff_rate = 0.0
            if dropoff_rate > worst_dropoff:
                worst_dropoff = dropoff_rate
                bottleneck_step = step_name

        steps.append(
            {
                "step_index": int(step_index),
                "step_name": str(step_name),
                "users_count": users,
                "conversion_rate": float(conversion_rate),
                "dropoff_rate": float(dropoff_rate),
            }
        )
        prev = users

    return {
        "total_users": total_users,
        "bottleneck_step": bottleneck_step,
        "steps": steps,
    }


def _require_project_editor_access(cur, user_id: str, project_id: str):
    cur.execute(
        """
        select 1
        from projects p
        join workspace_members wm on wm.workspace_id = p.workspace_id
        where p.id = %s::uuid
          and wm.user_id = %s::uuid
          and wm.role in ('owner', 'editor')
        limit 1
        """,
        (project_id, user_id),
    )
    if not cur.fetchone():
        raise PermissionError("Not allowed for this project")


def _ensure_experiment(
    cur,
    user_id: str,
    project_id: str,
    experiment_id: str | None,
    hypothesis: str,
    primary_metric: str,
    guardrail_metrics: list[str],
) -> str:
    if experiment_id:
        cur.execute(
            """
            select e.id::text
            from experiments e
            join projects p on p.id = e.project_id
            join workspace_members wm on wm.workspace_id = p.workspace_id
            where e.id = %s::uuid
              and e.project_id = %s::uuid
              and wm.user_id = %s::uuid
              and wm.role in ('owner', 'editor')
            limit 1
            """,
            (experiment_id, project_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            raise PermissionError("Experiment not accessible")
        return str(row[0])

    cur.execute(
        """
        insert into experiments (
            project_id, hypothesis, primary_metric, guardrail_metrics, status, created_by, started_at
        )
        values (
            %s::uuid,
            'Simulated checkout uplift by CTA/UI changes',
            %s,
            %s::jsonb,
            'active',
            %s::uuid,
            now()
        )
        returning id::text
        """,
        (
            project_id,
            hypothesis,
            primary_metric,
            json.dumps(guardrail_metrics),
            user_id,
        ),
    )
    row = cur.fetchone()
    return str(row[0])


def _ensure_default_variants(cur, experiment_id: str):
    cur.execute(
        """
        insert into variants (experiment_id, variant_key, config_json, traffic_weight)
        values
            (%s::uuid, 'control', '{"label":"Current"}'::jsonb, 50.00),
            (%s::uuid, 'test', '{"label":"Proposed"}'::jsonb, 50.00)
        on conflict (experiment_id, variant_key) do nothing
        """,
        (experiment_id, experiment_id),
    )


def bootstrap_simulation_for_project(
    user_id: str,
    project_id: str,
    body: SimulationBootstrapRequest,
) -> dict:
    run_id = body.run_id or f"sim_{dt.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    rng = random.Random(body.seed)
    template = resolve_template_settings(body.template)
    step_plan = resolve_template_steps(body.template)
    challenge_defs = resolve_template_sql_challenges(body.template)
    preset_defaults = resolve_template_seed_preset(body.template, body.seed_preset)
    control_rate = (
        float(body.control_purchase_rate)
        if body.control_purchase_rate is not None
        else float(preset_defaults["control_purchase_rate"])
    )
    test_rate = (
        float(body.test_purchase_rate)
        if body.test_purchase_rate is not None
        else float(preset_defaults["test_purchase_rate"])
    )
    user_count = (
        int(body.user_count)
        if body.user_count is not None
        else int(preset_defaults["user_count"])
    )

    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            _require_project_editor_access(cur, user_id, project_id)
            experiment_id = _ensure_experiment(
                cur,
                user_id,
                project_id,
                body.experiment_id,
                hypothesis=str(template["hypothesis"]),
                primary_metric=str(template["primary_metric"]),
                guardrail_metrics=list(template["guardrail_metrics"]),
            )
            _ensure_default_variants(cur, experiment_id)

            control_probs = _build_conditional_probs(step_plan, control_rate)
            test_probs = _build_conditional_probs(step_plan, test_rate)

            assignments_rows = []
            events_rows = []
            control_users = 0
            test_users = 0
            now = dt.datetime.utcnow()

            for idx in range(user_count):
                user_key = f"{run_id}_u_{idx:06d}"
                is_test = rng.random() < body.test_split
                variant_key = "test" if is_test else "control"
                if is_test:
                    test_users += 1
                else:
                    control_users += 1

                assignments_rows.append(
                    (
                        project_id,
                        experiment_id,
                        user_key,
                        variant_key,
                        now + dt.timedelta(seconds=idx % 60),
                        run_id,
                        1.0,
                    )
                )

                probs = test_probs if is_test else control_probs
                names = _simulate_user_events(rng, step_plan, probs)
                for step_idx, event_name in enumerate(names):
                    event_value = round(20.0 + rng.random() * 180.0, 2) if event_name == "purchase" else 0.0
                    props = {"variant_key": variant_key, "source": "simulation_v2", "template": body.template}
                    events_rows.append(
                        (
                            project_id,
                            experiment_id,
                            user_key,
                            run_id,
                            event_name,
                            now + dt.timedelta(seconds=(idx % 60) + step_idx),
                            event_value,
                            json.dumps(props),
                        )
                    )

            execute_values(
                cur,
                """
                insert into assignments (
                    project_id, experiment_id, user_key, variant_key, assigned_at, run_id, weight
                ) values %s
                """,
                assignments_rows,
                page_size=1000,
            )

            execute_values(
                cur,
                """
                insert into events (
                    project_id, experiment_id, user_key, run_id, event_name, event_time, value, props_json
                ) values %s
                """,
                events_rows,
                page_size=2000,
            )

            seeded_count = 0
            if body.seed_sql_challenges:
                for ch in challenge_defs:
                    title = f"[Starter:{body.template}] {ch['title']}"
                    cur.execute(
                        """
                        insert into sql_challenges (
                            project_id, title, prompt_md, difficulty, expected_schema, expected_metrics
                        )
                        select %s::uuid, %s, %s, %s, %s::jsonb, %s::jsonb
                        where not exists (
                            select 1 from sql_challenges
                            where project_id = %s::uuid
                              and title = %s
                        )
                        """,
                        (
                            project_id,
                            title,
                            (
                                f"{ch['prompt_md']}\n\n"
                                f"Starter SQL:\n```sql\n{ch['starter_sql']}\n```"
                            ),
                            ch["difficulty"],
                            json.dumps(ch["expected_schema"]),
                            json.dumps(ch["expected_metrics"]),
                            project_id,
                            title,
                        ),
                    )
                    seeded_count += int(cur.rowcount or 0)
            else:
                seeded_count = 0

    return {
        "project_id": project_id,
        "experiment_id": experiment_id,
        "run_id": run_id,
        "template": body.template,
        "seed_preset": body.seed_preset,
        "user_count": user_count,
        "assignments_inserted": len(assignments_rows),
        "events_inserted": len(events_rows),
        "control_users": control_users,
        "test_users": test_users,
        "control_purchase_rate": control_rate,
        "test_purchase_rate": test_rate,
        "sql_challenges_seeded": seeded_count,
    }


def _resolve_funnel_template_for_scope(
    user_id: str,
    project_id: str,
    run_id: str | None,
    experiment_id: str | None,
) -> str:
    where_parts = ["e.project_id = %s::uuid"]
    params: list = [project_id]
    if run_id:
        where_parts.append("coalesce(e.run_id, '') = %s")
        params.append(run_id)
    if experiment_id:
        where_parts.append("e.experiment_id = %s::uuid")
        params.append(experiment_id)
    where_sql = " and ".join(where_parts)

    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                select coalesce(e.props_json->>'template', 'commerce') as template_key, count(*) as c
                from events e
                where {where_sql}
                group by template_key
                order by c desc
                limit 1
                """,
                tuple(params),
            )
            row = cur.fetchone()
    template_key = str(row[0]) if row and row[0] else "commerce"
    if template_key not in TEMPLATE_STEP_PLANS:
        return "commerce"
    return template_key


def get_funnel_overview_for_user(
    user_id: str,
    project_id: str,
    run_id: str | None,
    experiment_id: str | None,
    template: str | None = None,
) -> dict:
    where_parts = ["e.project_id = %s::uuid"]
    params = [project_id]
    if run_id:
        where_parts.append("coalesce(e.run_id, '') = %s")
        params.append(run_id)
    if experiment_id:
        where_parts.append("e.experiment_id = %s::uuid")
        params.append(experiment_id)

    template_key = template or _resolve_funnel_template_for_scope(
        user_id=user_id,
        project_id=project_id,
        run_id=run_id,
        experiment_id=experiment_id,
    )
    step_plan = resolve_template_steps(template_key)
    where_sql = " and ".join(where_parts)

    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                select
                    e.event_name,
                    count(distinct e.user_key) as users_count
                from events e
                where {where_sql}
                  and e.event_name = any(%s)
                group by e.event_name
                """,
                tuple(params + [step_plan]),
            )
            rows = cur.fetchall()

    counts_map = {str(r[0]): int(r[1]) for r in rows}
    steps_with_counts = [
        (idx, step_name, counts_map.get(step_name, 0))
        for idx, step_name in enumerate(step_plan)
    ]
    overview = compute_funnel_overview(steps_with_counts)
    return {
        "project_id": project_id,
        "run_id": run_id,
        "experiment_id": experiment_id,
        "template": template_key,
        "total_users": overview["total_users"],
        "bottleneck_step": overview["bottleneck_step"],
        "steps": overview["steps"],
    }
