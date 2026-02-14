from apps.api.db.session import get_db_conn


def get_portfolio_for_user(user_id: str) -> dict:
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select
                    count(*) as experiments_total,
                    count(*) filter (where er.decision = 'adopt') as experiments_adopted,
                    coalesce(avg(er.lift), 0.0) as avg_lift
                from experiments e
                join projects p on p.id = e.project_id
                join workspace_members wm on wm.workspace_id = p.workspace_id
                left join experiment_results er on er.experiment_id = e.id
                where wm.user_id = %s::uuid
                """,
                (user_id,),
            )
            exp_row = cur.fetchone()

            cur.execute(
                """
                select
                    count(*) as sql_submissions_total,
                    count(*) filter (where ss.is_correct) as sql_correct_total
                from sql_submissions ss
                where ss.user_id = %s::uuid
                """,
                (user_id,),
            )
            sql_row = cur.fetchone()

            cur.execute(
                """
                select count(*)
                from journey_events je
                join user_journeys uj on uj.id = je.journey_id
                where uj.user_id = %s::uuid
                """,
                (user_id,),
            )
            journey_count = cur.fetchone()[0]

            cur.execute(
                """
                select
                    e.id::text,
                    e.hypothesis,
                    er.decision,
                    e.created_at::text
                from experiments e
                join projects p on p.id = e.project_id
                join workspace_members wm on wm.workspace_id = p.workspace_id
                left join experiment_results er on er.experiment_id = e.id
                where wm.user_id = %s::uuid
                order by e.created_at desc
                limit 10
                """,
                (user_id,),
            )
            recent_rows = cur.fetchall()

    sql_total = int(sql_row[0] or 0)
    sql_correct = int(sql_row[1] or 0)
    sql_accuracy = (sql_correct / sql_total) if sql_total > 0 else 0.0

    return {
        "summary": {
            "experiments_total": int(exp_row[0] or 0),
            "experiments_adopted": int(exp_row[1] or 0),
            "avg_lift": float(exp_row[2] or 0.0),
            "sql_submissions_total": sql_total,
            "sql_correct_total": sql_correct,
            "sql_accuracy": sql_accuracy,
            "journey_events_total": int(journey_count or 0),
        },
        "recent_experiments": [
            {
                "experiment_id": row[0],
                "hypothesis": row[1],
                "decision": row[2],
                "created_at": row[3],
            }
            for row in recent_rows
        ],
    }

