import json
import re

from apps.api.db.session import get_db_conn
from apps.api.schemas.community import (
    CommunityCommentCreateRequest,
    CommunityForkCreateRequest,
    CommunityPostCreateRequest,
)


_TAG_PATTERN = re.compile(r"^[a-z0-9_-]{1,24}$")


def normalize_tags(tags: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in tags:
        tag = raw.strip().lower()
        if not tag:
            continue
        if not _TAG_PATTERN.match(tag):
            continue
        if tag in seen:
            continue
        seen.add(tag)
        normalized.append(tag)
        if len(normalized) >= 10:
            break
    return normalized


def list_posts_for_user(
    user_id: str,
    project_id: str | None = None,
    limit: int = 50,
    sort_by: str = "recent",
) -> list[dict]:
    where_clause = ""
    params: list = [user_id]
    if project_id:
        where_clause = "and cp.project_id = %s::uuid"
        params.append(project_id)
    params.append(limit)

    order_clause = "cp.created_at desc"
    if sort_by == "ranked":
        order_clause = "rank_score desc, cp.created_at desc"

    sql = f"""
        select
            cp.id::text,
            cp.project_id::text,
            cp.experiment_id::text,
            cp.author_user_id::text,
            cp.title,
            cp.body_md,
            cp.tags,
            cp.created_at::text,
            coalesce(cc.comment_count, 0) as comment_count,
            coalesce(fk.fork_count, 0) as fork_count,
            (
                (coalesce(cc.comment_count, 0) * 3.0) +
                (coalesce(fk.fork_count, 0) * 5.0) +
                greatest(
                    0.0,
                    (72.0 - (extract(epoch from (now() - cp.created_at)) / 3600.0)) / 72.0
                )
            ) as rank_score
        from community_posts cp
        left join (
            select post_id, count(*)::int as comment_count
            from community_comments
            group by post_id
        ) cc on cc.post_id = cp.id
        left join (
            select source_experiment_id, count(*)::int as fork_count
            from experiment_forks
            group by source_experiment_id
        ) fk on fk.source_experiment_id = cp.experiment_id
        join projects p on p.id = cp.project_id
        join workspace_members wm on wm.workspace_id = p.workspace_id
        where wm.user_id = %s::uuid
        {where_clause}
        order by {order_clause}
        limit %s
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
    return [
        {
            "id": row[0],
            "project_id": row[1],
            "experiment_id": row[2],
            "author_user_id": row[3],
            "title": row[4],
            "body_md": row[5],
            "tags": row[6] or [],
            "created_at": row[7],
            "comment_count": int(row[8] or 0),
            "fork_count": int(row[9] or 0),
            "rank_score": float(row[10] or 0.0),
        }
        for row in rows
    ]


def compute_rank_score(comment_count: int, fork_count: int, age_hours: float) -> float:
    freshness = max(0.0, (72.0 - age_hours) / 72.0)
    return (float(comment_count) * 3.0) + (float(fork_count) * 5.0) + freshness


def create_post_for_user(user_id: str, body: CommunityPostCreateRequest) -> dict:
    tags = normalize_tags(body.tags)
    sql = """
        insert into community_posts (
            project_id, experiment_id, author_user_id, title, body_md, tags
        )
        select %s::uuid, %s::uuid, %s::uuid, %s, %s, %s::text[]
        where exists (
            select 1
            from projects p
            join workspace_members wm on wm.workspace_id = p.workspace_id
            where p.id = %s::uuid
              and wm.user_id = %s::uuid
        )
        returning
            id::text, project_id::text, experiment_id::text, author_user_id::text,
            title, body_md, tags, created_at::text
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    body.project_id,
                    body.experiment_id,
                    user_id,
                    body.title,
                    body.body_md,
                    tags,
                    body.project_id,
                    user_id,
                ),
            )
            row = cur.fetchone()
    if not row:
        raise PermissionError("Not allowed to create post for this project")
    return {
        "id": row[0],
        "project_id": row[1],
        "experiment_id": row[2],
        "author_user_id": row[3],
        "title": row[4],
        "body_md": row[5],
        "tags": row[6] or [],
        "created_at": row[7],
    }


def list_comments_for_user(user_id: str, post_id: str, limit: int = 100) -> list[dict]:
    sql = """
        select
            cc.id,
            cc.post_id::text,
            cc.author_user_id::text,
            cc.body_md,
            cc.created_at::text
        from community_comments cc
        join community_posts cp on cp.id = cc.post_id
        join projects p on p.id = cp.project_id
        join workspace_members wm on wm.workspace_id = p.workspace_id
        where cc.post_id = %s::uuid
          and wm.user_id = %s::uuid
        order by cc.created_at asc
        limit %s
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (post_id, user_id, limit))
            rows = cur.fetchall()
    return [
        {
            "id": row[0],
            "post_id": row[1],
            "author_user_id": row[2],
            "body_md": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]


def create_comment_for_user(
    user_id: str, post_id: str, body: CommunityCommentCreateRequest
) -> dict:
    sql = """
        insert into community_comments (post_id, author_user_id, body_md)
        select %s::uuid, %s::uuid, %s
        where exists (
            select 1
            from community_posts cp
            join projects p on p.id = cp.project_id
            join workspace_members wm on wm.workspace_id = p.workspace_id
            where cp.id = %s::uuid
              and wm.user_id = %s::uuid
        )
        returning id, post_id::text, author_user_id::text, body_md, created_at::text
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (post_id, user_id, body.body_md, post_id, user_id))
            row = cur.fetchone()
    if not row:
        raise PermissionError("Not allowed to comment on this post")
    return {
        "id": row[0],
        "post_id": row[1],
        "author_user_id": row[2],
        "body_md": row[3],
        "created_at": row[4],
    }


def fork_experiment_for_user(user_id: str, body: CommunityForkCreateRequest) -> dict:
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select
                    e.hypothesis,
                    e.primary_metric,
                    e.guardrail_metrics
                from experiments e
                join projects p on p.id = e.project_id
                join workspace_members wm on wm.workspace_id = p.workspace_id
                where e.id = %s::uuid
                  and wm.user_id = %s::uuid
                limit 1
                """,
                (body.source_experiment_id, user_id),
            )
            source = cur.fetchone()
            if not source:
                raise PermissionError("Source experiment is not accessible")

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
                (body.target_project_id, user_id),
            )
            allowed = cur.fetchone() is not None
            if not allowed:
                raise PermissionError("Not allowed to fork into target project")

            fork_hypothesis = f"[Fork] {source[0]}"
            cur.execute(
                """
                insert into experiments (
                    project_id, hypothesis, primary_metric, guardrail_metrics, status, created_by
                )
                values (%s::uuid, %s, %s, %s::jsonb, 'draft', %s::uuid)
                returning id::text, created_at::text
                """,
                (
                    body.target_project_id,
                    fork_hypothesis,
                    source[1],
                    json.dumps(source[2] or []),
                    user_id,
                ),
            )
            forked = cur.fetchone()

            cur.execute(
                """
                insert into experiment_forks (source_experiment_id, forked_experiment_id, forked_by)
                values (%s::uuid, %s::uuid, %s::uuid)
                returning source_experiment_id::text, forked_experiment_id::text, forked_by::text, created_at::text
                """,
                (body.source_experiment_id, forked[0], user_id),
            )
            row = cur.fetchone()

    return {
        "source_experiment_id": row[0],
        "forked_experiment_id": row[1],
        "forked_by": row[2],
        "created_at": row[3],
    }
