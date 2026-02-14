import argparse
import json

from apps.api.db.session import get_db_conn


def _collect_stale_run_ids(cur, retention_days: int, run_prefix: str) -> list[str]:
    cur.execute(
        """
        with stale_runs as (
            select run_id
            from events
            where run_id is not null
              and run_id like %s
            group by run_id
            having max(event_time) < now() - make_interval(days => %s)
        )
        select run_id
        from stale_runs
        order by run_id
        """,
        (f"{run_prefix}%", retention_days),
    )
    return [str(row[0]) for row in cur.fetchall()]


def _collect_stale_run_ids_workspace_policy(
    cur,
    fallback_retention_days: int,
    run_prefix: str,
) -> list[str]:
    cur.execute(
        """
        with run_scope as (
            select
                e.run_id,
                coalesce(w.simulation_retention_days, %s) as retention_days,
                max(e.event_time) as max_event_time
            from events e
            join projects p on p.id = e.project_id
            join workspaces w on w.id = p.workspace_id
            where e.run_id is not null
              and e.run_id like %s
            group by e.run_id, coalesce(w.simulation_retention_days, %s)
        )
        select run_id
        from run_scope
        where max_event_time < now() - make_interval(days => retention_days)
        order by run_id
        """,
        (fallback_retention_days, f"{run_prefix}%", fallback_retention_days),
    )
    return [str(row[0]) for row in cur.fetchall()]


def _count_table_rows(cur, run_ids: list[str], table: str) -> int:
    if not run_ids:
        return 0
    cur.execute(
        f"""
        select count(*)
        from {table}
        where run_id = any(%s)
        """,
        (run_ids,),
    )
    row = cur.fetchone()
    return int(row[0]) if row else 0


def _delete_table_rows(cur, run_ids: list[str], table: str) -> int:
    if not run_ids:
        return 0
    cur.execute(
        f"""
        delete from {table}
        where run_id = any(%s)
        """,
        (run_ids,),
    )
    return int(cur.rowcount or 0)


def cleanup_stale_simulations(
    retention_days: int,
    run_prefix: str,
    apply: bool,
    respect_workspace_policy: bool,
) -> dict:
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            if respect_workspace_policy:
                run_ids = _collect_stale_run_ids_workspace_policy(
                    cur,
                    fallback_retention_days=retention_days,
                    run_prefix=run_prefix,
                )
            else:
                run_ids = _collect_stale_run_ids(cur, retention_days, run_prefix)

            counts_before = {
                "events": _count_table_rows(cur, run_ids, "events"),
                "assignments": _count_table_rows(cur, run_ids, "assignments"),
                "experiment_results": _count_table_rows(cur, run_ids, "experiment_results"),
            }

            deleted = {"events": 0, "assignments": 0, "experiment_results": 0}
            if apply and run_ids:
                # child-like derived rows first, then events
                deleted["experiment_results"] = _delete_table_rows(cur, run_ids, "experiment_results")
                deleted["assignments"] = _delete_table_rows(cur, run_ids, "assignments")
                deleted["events"] = _delete_table_rows(cur, run_ids, "events")

    return {
        "retention_days": retention_days,
        "run_prefix": run_prefix,
        "candidate_runs": len(run_ids),
        "sample_run_ids": run_ids[:10],
        "counts_before": counts_before,
        "deleted": deleted,
        "applied": apply,
        "respect_workspace_policy": respect_workspace_policy,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Cleanup stale simulation runs by run_id prefix.")
    parser.add_argument("--retention-days", type=int, default=30, help="Delete runs older than N days.")
    parser.add_argument(
        "--run-prefix",
        type=str,
        default="sim_",
        help="Target run_id prefix (default: sim_).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply deletion. If omitted, only dry-run counts are printed.",
    )
    parser.add_argument(
        "--respect-workspace-policy",
        action="store_true",
        help="Use each workspace's simulation_retention_days instead of global retention days.",
    )
    args = parser.parse_args()

    if args.retention_days <= 0:
        raise SystemExit("--retention-days must be positive")

    summary = cleanup_stale_simulations(
        retention_days=args.retention_days,
        run_prefix=args.run_prefix,
        apply=args.apply,
        respect_workspace_policy=bool(args.respect_workspace_policy),
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
