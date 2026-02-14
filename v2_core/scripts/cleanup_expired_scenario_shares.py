import argparse
import json

from apps.api.db.session import get_db_conn


def _collect_candidates(cur, include_revoked: bool) -> list[str]:
    if include_revoked:
        cur.execute(
            """
            select id::text
            from scenario_share_links
            where expires_at < now()
               or revoked_at is not null
            order by created_at asc
            """
        )
    else:
        cur.execute(
            """
            select id::text
            from scenario_share_links
            where expires_at < now()
            order by created_at asc
            """
        )
    return [str(row[0]) for row in cur.fetchall()]


def _count_rows(cur, share_ids: list[str]) -> int:
    if not share_ids:
        return 0
    cur.execute(
        """
        select count(*)
        from scenario_share_links
        where id::text = any(%s)
        """,
        (share_ids,),
    )
    row = cur.fetchone()
    return int(row[0]) if row else 0


def _delete_rows(cur, share_ids: list[str]) -> int:
    if not share_ids:
        return 0
    cur.execute(
        """
        delete from scenario_share_links
        where id::text = any(%s)
        """,
        (share_ids,),
    )
    return int(cur.rowcount or 0)


def cleanup_expired_scenario_shares(apply: bool, include_revoked: bool) -> dict:
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            share_ids = _collect_candidates(cur, include_revoked=include_revoked)
            counts_before = {"scenario_share_links": _count_rows(cur, share_ids)}
            deleted = {"scenario_share_links": 0}

            if apply and share_ids:
                deleted["scenario_share_links"] = _delete_rows(cur, share_ids)

    return {
        "candidate_links": len(share_ids),
        "sample_share_ids": share_ids[:10],
        "counts_before": counts_before,
        "deleted": deleted,
        "applied": apply,
        "include_revoked": include_revoked,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Cleanup expired scenario share links.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply deletion. If omitted, only dry-run counts are printed.",
    )
    parser.add_argument(
        "--include-revoked",
        action="store_true",
        help="Also purge links already revoked, not only expired.",
    )
    args = parser.parse_args()

    summary = cleanup_expired_scenario_shares(
        apply=args.apply,
        include_revoked=bool(args.include_revoked),
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
