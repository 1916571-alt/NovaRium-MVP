import math

from apps.api.db.session import get_db_conn


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _p_value_from_z(z: float) -> float:
    return max(0.0, min(1.0, 2.0 * (1.0 - _normal_cdf(abs(z)))))


def _srm_p_value(control_users: int, test_users: int, expected_ratio: float = 0.5) -> float:
    total = control_users + test_users
    if total <= 0:
        return 1.0
    exp_c = total * expected_ratio
    exp_t = total * (1 - expected_ratio)
    if exp_c <= 0 or exp_t <= 0:
        return 1.0
    chi2 = ((control_users - exp_c) ** 2 / exp_c) + ((test_users - exp_t) ** 2 / exp_t)
    # For df=1, survival function is erfc(sqrt(chi2/2))
    return float(math.erfc(math.sqrt(chi2 / 2.0)))


def calculate_ab_stats(
    control_users: int,
    control_conversions: int,
    test_users: int,
    test_conversions: int,
) -> dict:
    c_rate = (control_conversions / control_users) if control_users > 0 else 0.0
    t_rate = (test_conversions / test_users) if test_users > 0 else 0.0
    lift = ((t_rate - c_rate) / c_rate) if c_rate > 0 else 0.0

    z_score = 0.0
    p_value = 1.0
    ci_lower = 0.0
    ci_upper = 0.0

    if control_users > 0 and test_users > 0:
        pooled = (control_conversions + test_conversions) / (control_users + test_users)
        se = math.sqrt(max(0.0, pooled * (1.0 - pooled) * (1.0 / control_users + 1.0 / test_users)))
        if se > 0:
            z_score = (t_rate - c_rate) / se
            p_value = _p_value_from_z(z_score)

        # Difference CI then convert to relative lift CI.
        var_diff = (
            (c_rate * (1.0 - c_rate) / control_users)
            + (t_rate * (1.0 - t_rate) / test_users)
        )
        se_diff = math.sqrt(max(0.0, var_diff))
        z_crit = 1.959963984540054
        diff = t_rate - c_rate
        diff_lower = diff - z_crit * se_diff
        diff_upper = diff + z_crit * se_diff
        if c_rate > 0:
            ci_lower = diff_lower / c_rate
            ci_upper = diff_upper / c_rate

    srm_p = _srm_p_value(control_users, test_users, expected_ratio=0.5)
    srm_detected = srm_p < 0.01

    if srm_detected:
        recommendation = "invalid_srm"
    elif p_value < 0.05 and lift > 0:
        recommendation = "adopt"
    elif p_value < 0.05 and lift < 0:
        recommendation = "reject"
    else:
        recommendation = "inconclusive"

    return {
        "control_rate": c_rate,
        "test_rate": t_rate,
        "lift": lift,
        "z_score": z_score,
        "p_value": p_value,
        "srm_p_value": srm_p,
        "srm_detected": srm_detected,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "recommendation": recommendation,
    }


def _resolve_metric_event(primary_metric: str) -> str:
    lower = (primary_metric or "").lower()
    if "ctr" in lower or "click" in lower:
        return "click_cta"
    return "purchase"


def analyze_experiment_run_for_user(user_id: str, experiment_id: str, run_id: str) -> dict:
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select e.primary_metric
                from experiments e
                join projects p on p.id = e.project_id
                join workspace_members wm on wm.workspace_id = p.workspace_id
                where e.id = %s::uuid
                  and wm.user_id = %s::uuid
                limit 1
                """,
                (experiment_id, user_id),
            )
            row = cur.fetchone()
            if not row:
                raise PermissionError("Experiment not accessible")
            primary_metric = row[0]
            metric_event = _resolve_metric_event(primary_metric)

            cur.execute(
                """
                select
                    a.variant_key,
                    count(distinct a.user_key) as users,
                    count(distinct case when e.event_name = %s then e.user_key end) as conversions
                from assignments a
                left join events e
                  on e.experiment_id = a.experiment_id
                 and e.user_key = a.user_key
                 and coalesce(e.run_id, '') = coalesce(a.run_id, '')
                where a.experiment_id = %s::uuid
                  and a.run_id = %s
                group by a.variant_key
                order by a.variant_key asc
                """,
                (metric_event, experiment_id, run_id),
            )
            rows = cur.fetchall()

    if len(rows) < 2:
        raise ValueError("Need at least two variants with assignment data")

    control_variant, control_users, control_conversions = rows[0]
    test_variant, test_users, test_conversions = rows[1]
    stats = calculate_ab_stats(
        int(control_users),
        int(control_conversions),
        int(test_users),
        int(test_conversions),
    )

    return {
        "experiment_id": experiment_id,
        "run_id": run_id,
        "metric_event": metric_event,
        "control_variant": str(control_variant),
        "test_variant": str(test_variant),
        "control_users": int(control_users),
        "control_conversions": int(control_conversions),
        "test_users": int(test_users),
        "test_conversions": int(test_conversions),
        "control_rate": stats["control_rate"],
        "test_rate": stats["test_rate"],
        "lift": stats["lift"],
        "z_score": stats["z_score"],
        "p_value": stats["p_value"],
        "srm_p_value": stats["srm_p_value"],
        "srm_detected": stats["srm_detected"],
        "ci_lower": stats["ci_lower"],
        "ci_upper": stats["ci_upper"],
        "recommendation": stats["recommendation"],
    }


def persist_experiment_analysis_for_user(user_id: str, analysis: dict) -> dict:
    sql = """
        insert into experiment_results (
            experiment_id, run_id,
            control_users, control_conversions,
            test_users, test_conversions,
            lift, p_value, ci_lower, ci_upper,
            srm_p_value, decision, decided_by, decided_at
        )
        values (
            %s::uuid, %s,
            %s, %s,
            %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s::uuid, now()
        )
        on conflict (experiment_id, run_id)
        do update set
            control_users = excluded.control_users,
            control_conversions = excluded.control_conversions,
            test_users = excluded.test_users,
            test_conversions = excluded.test_conversions,
            lift = excluded.lift,
            p_value = excluded.p_value,
            ci_lower = excluded.ci_lower,
            ci_upper = excluded.ci_upper,
            srm_p_value = excluded.srm_p_value,
            decision = excluded.decision,
            decided_by = excluded.decided_by,
            decided_at = excluded.decided_at,
            created_at = now()
        returning
            id,
            experiment_id::text,
            run_id,
            decision,
            created_at::text
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    analysis["experiment_id"],
                    analysis["run_id"],
                    analysis["control_users"],
                    analysis["control_conversions"],
                    analysis["test_users"],
                    analysis["test_conversions"],
                    analysis["lift"],
                    analysis["p_value"],
                    analysis["ci_lower"],
                    analysis["ci_upper"],
                    analysis["srm_p_value"],
                    analysis["recommendation"],
                    user_id,
                ),
            )
            row = cur.fetchone()
    return {
        "id": row[0],
        "experiment_id": row[1],
        "run_id": row[2],
        "decision": row[3],
        "created_at": row[4],
    }
