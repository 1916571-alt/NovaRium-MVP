import datetime as dt
import decimal
import json
import re

from apps.api.db.session import get_db_conn
from apps.api.schemas.sql_lab import (
    SqlChallengeCreateRequest,
    SqlSnippetCreateRequest,
    SqlSnippetUpdateRequest,
    SqlSubmissionCreateRequest,
)


_DISALLOWED_SQL_PATTERN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|vacuum|analyze)\b",
    flags=re.IGNORECASE,
)
_TAG_PATTERN = re.compile(r"^[a-z0-9_-]{1,24}$")


def normalize_snippet_tags(tags: list[str]) -> list[str]:
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


def _normalize_query(query: str) -> str:
    return query.strip().rstrip(";").strip()


def validate_readonly_sql(query: str) -> str:
    normalized = _normalize_query(query)
    if not normalized:
        raise ValueError("Query is empty")

    statements = [x.strip() for x in normalized.split(";") if x.strip()]
    if len(statements) > 1:
        raise ValueError("Only a single SQL statement is allowed")

    first = normalized.split(None, 1)[0].lower() if normalized.split() else ""
    if first not in {"select", "with"}:
        raise ValueError("Only SELECT/WITH queries are allowed")

    if _DISALLOWED_SQL_PATTERN.search(normalized):
        raise ValueError("Mutation/DDL keywords are not allowed in SQL Lab")

    return normalized


def _to_json_value(value):
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    return str(value)


def _is_number(value) -> bool:
    return isinstance(value, (int, float, decimal.Decimal))


def _cell_equal(actual, expected, tolerance: float) -> bool:
    if _is_number(actual) and _is_number(expected):
        return abs(float(actual) - float(expected)) <= tolerance
    return actual == expected


def _row_object_from_result(columns: list[str], row: list) -> dict:
    return {columns[i]: row[i] for i in range(min(len(columns), len(row)))}


def _match_expected_rows(
    columns: list[str],
    actual_rows: list[list],
    expected_rows: list[dict],
    tolerance: float,
    unordered: bool,
) -> tuple[bool, dict]:
    actual_objs = [_row_object_from_result(columns, r) for r in actual_rows]

    if unordered:
        used = [False] * len(actual_objs)
        missing: list[dict] = []
        for expected in expected_rows:
            found = False
            for idx, actual in enumerate(actual_objs):
                if used[idx]:
                    continue
                keys = expected.keys()
                if all(_cell_equal(actual.get(k), expected.get(k), tolerance) for k in keys):
                    used[idx] = True
                    found = True
                    break
            if not found:
                missing.append(expected)
        ok = len(missing) == 0
        return ok, {"missing_rows": missing}

    # Ordered comparison: each expected row must match the row at same index.
    if len(actual_objs) < len(expected_rows):
        return False, {"reason": "actual_rows_shorter_than_expected"}

    mismatch: list[dict] = []
    for i, expected in enumerate(expected_rows):
        actual = actual_objs[i]
        keys = expected.keys()
        ok_row = all(_cell_equal(actual.get(k), expected.get(k), tolerance) for k in keys)
        if not ok_row:
            mismatch.append({"index": i, "expected": expected, "actual": actual})
    ok = len(mismatch) == 0
    return ok, {"mismatch_rows": mismatch}


def execute_readonly_sql(user_id: str, query: str, max_rows: int) -> dict:
    normalized = validate_readonly_sql(query)
    wrapped_sql = f"select * from ({normalized}) as q limit %s"

    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute("set local statement_timeout = 5000")
            cur.execute("set local transaction read only")
            cur.execute(wrapped_sql, (max_rows + 1,))
            rows = cur.fetchall()
            columns = [d[0] for d in cur.description] if cur.description else []

    truncated = len(rows) > max_rows
    rows = rows[:max_rows]
    return {
        "columns": columns,
        "rows": [[_to_json_value(v) for v in row] for row in rows],
        "row_count": len(rows),
        "truncated": truncated,
    }


def grade_submission_result(
    result: dict,
    expected_schema: dict | None,
    expected_metrics: dict | None,
) -> tuple[bool, dict]:
    expected_schema = expected_schema or {}
    expected_metrics = expected_metrics or {}

    actual_columns = list(result.get("columns", []))
    actual_row_count = int(result.get("row_count", 0))
    actual_rows = result.get("rows", []) or []
    tolerance = float(expected_metrics.get("numeric_tolerance", 0.0))
    unordered_rows = bool(expected_metrics.get("unordered_rows", True))

    checks: list[dict] = []
    passed = True

    schema_columns = expected_schema.get("columns")
    if schema_columns:
        expected_cols = [str(x) for x in schema_columns]
        ok = actual_columns == expected_cols
        checks.append(
            {
                "name": "schema.columns_exact",
                "ok": ok,
                "expected": expected_cols,
                "actual": actual_columns,
            }
        )
        passed = passed and ok

    must_have_columns = expected_metrics.get("must_have_columns")
    if must_have_columns:
        required = {str(x) for x in must_have_columns}
        actual_set = set(actual_columns)
        missing = sorted(required - actual_set)
        ok = len(missing) == 0
        checks.append(
            {
                "name": "metrics.must_have_columns",
                "ok": ok,
                "missing": missing,
            }
        )
        passed = passed and ok

    expected_row_count = expected_metrics.get("row_count")
    if expected_row_count is not None:
        expected_count = int(expected_row_count)
        ok = actual_row_count == expected_count
        checks.append(
            {
                "name": "metrics.row_count",
                "ok": ok,
                "expected": expected_count,
                "actual": actual_row_count,
            }
        )
        passed = passed and ok

    min_row_count = expected_metrics.get("min_row_count")
    if min_row_count is not None:
        min_count = int(min_row_count)
        ok = actual_row_count >= min_count
        checks.append(
            {
                "name": "metrics.min_row_count",
                "ok": ok,
                "expected": min_count,
                "actual": actual_row_count,
            }
        )
        passed = passed and ok

    max_row_count = expected_metrics.get("max_row_count")
    if max_row_count is not None:
        max_count = int(max_row_count)
        ok = actual_row_count <= max_count
        checks.append(
            {
                "name": "metrics.max_row_count",
                "ok": ok,
                "expected": max_count,
                "actual": actual_row_count,
            }
        )
        passed = passed and ok

    expected_rows = expected_metrics.get("expected_rows")
    if expected_rows:
        ok, detail = _match_expected_rows(
            columns=actual_columns,
            actual_rows=actual_rows,
            expected_rows=expected_rows,
            tolerance=tolerance,
            unordered=unordered_rows,
        )
        checks.append(
            {
                "name": "metrics.expected_rows",
                "ok": ok,
                "unordered": unordered_rows,
                **detail,
            }
        )
        passed = passed and ok

    # If no rule is provided, keep as not graded to avoid false pass.
    if not checks:
        return False, {"status": "pending_rules", "checks": []}

    return passed, {"status": "graded", "checks": checks}


def list_challenges_for_user(user_id: str, project_id: str | None) -> list[dict]:
    where_clause = ""
    params = [user_id]
    if project_id:
        where_clause = "and c.project_id = %s::uuid"
        params.append(project_id)

    sql = f"""
        select
            c.id::text,
            c.project_id::text,
            c.title,
            c.prompt_md,
            c.difficulty,
            c.created_at::text
        from sql_challenges c
        join projects p on p.id = c.project_id
        join workspace_members wm on wm.workspace_id = p.workspace_id
        where wm.user_id = %s::uuid
        {where_clause}
        order by c.created_at desc
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
    return [
        {
            "id": row[0],
            "project_id": row[1],
            "title": row[2],
            "prompt_md": row[3],
            "difficulty": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]


def create_challenge_for_user(user_id: str, body: SqlChallengeCreateRequest) -> dict:
    sql = """
        insert into sql_challenges (
            project_id, title, prompt_md, difficulty, expected_schema, expected_metrics
        )
        select %s::uuid, %s, %s, %s, %s::jsonb, %s::jsonb
        where exists (
            select 1
            from projects p
            join workspace_members wm on wm.workspace_id = p.workspace_id
            where p.id = %s::uuid
              and wm.user_id = %s::uuid
              and wm.role in ('owner', 'editor')
        )
        returning id::text, project_id::text, title, prompt_md, difficulty, created_at::text
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    body.project_id,
                    body.title,
                    body.prompt_md,
                    body.difficulty,
                    json.dumps(body.expected_schema),
                    json.dumps(body.expected_metrics),
                    body.project_id,
                    user_id,
                ),
            )
            row = cur.fetchone()
    if not row:
        raise PermissionError("Not allowed to create challenge for this project")
    return {
        "id": row[0],
        "project_id": row[1],
        "title": row[2],
        "prompt_md": row[3],
        "difficulty": row[4],
        "created_at": row[5],
    }


def submit_challenge_for_user(
    user_id: str, challenge_id: str, body: SqlSubmissionCreateRequest
) -> dict:
    access_sql = """
        select
            c.expected_schema,
            c.expected_metrics
        from sql_challenges c
        join projects p on p.id = c.project_id
        join workspace_members wm on wm.workspace_id = p.workspace_id
        where c.id = %s::uuid
          and wm.user_id = %s::uuid
        limit 1
    """

    execute_result = execute_readonly_sql(user_id, body.sql_text, 500)

    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(access_sql, (challenge_id, user_id))
            access_row = cur.fetchone()
            if not access_row:
                raise PermissionError("Challenge not accessible")

            expected_schema = access_row[0] or {}
            expected_metrics = access_row[1] or {}
            is_correct, feedback_json = grade_submission_result(
                execute_result,
                expected_schema,
                expected_metrics,
            )

            cur.execute(
                """
                insert into sql_submissions (challenge_id, user_id, sql_text, is_correct, feedback_json)
                values (%s::uuid, %s::uuid, %s, %s, %s::jsonb)
                returning id, challenge_id::text, user_id::text, is_correct, feedback_json, submitted_at::text
                """,
                (
                    challenge_id,
                    user_id,
                    body.sql_text,
                    is_correct,
                    json.dumps(feedback_json),
                ),
            )
            row = cur.fetchone()

    return {
        "id": row[0],
        "challenge_id": row[1],
        "user_id": row[2],
        "is_correct": row[3],
        "feedback_json": row[4],
        "submitted_at": row[5],
    }


def list_snippets_for_user(
    user_id: str,
    project_id: str | None,
    q: str | None = None,
    tag: str | None = None,
    pinned_only: bool = False,
) -> list[dict]:
    where_parts: list[str] = []
    params = [user_id]
    if project_id:
        where_parts.append("s.project_id = %s::uuid")
        params.append(project_id)
    if q and q.strip():
        where_parts.append("(s.title ilike %s or s.sql_text ilike %s)")
        needle = f"%{q.strip()}%"
        params.append(needle)
        params.append(needle)
    if tag and tag.strip():
        where_parts.append("%s = any(s.tags)")
        params.append(tag.strip().lower())
    if pinned_only:
        where_parts.append("s.is_pinned = true")

    where_clause = ""
    if where_parts:
        where_clause = "and " + " and ".join(where_parts)

    sql = f"""
        select
            s.id::text,
            s.project_id::text,
            s.author_user_id::text,
            s.title,
            s.sql_text,
            s.tags,
            s.is_pinned,
            s.pinned_at::text,
            s.created_at::text,
            s.updated_at::text
        from sql_snippets s
        join projects p on p.id = s.project_id
        join workspace_members wm on wm.workspace_id = p.workspace_id
        where wm.user_id = %s::uuid
        {where_clause}
        order by s.is_pinned desc, s.pinned_at desc nulls last, s.updated_at desc, s.created_at desc
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
    return [
        {
            "id": row[0],
            "project_id": row[1],
            "author_user_id": row[2],
            "title": row[3],
            "sql_text": row[4],
            "tags": row[5] or [],
            "is_pinned": bool(row[6]),
            "pinned_at": row[7],
            "created_at": row[8],
            "updated_at": row[9],
        }
        for row in rows
    ]


def create_snippet_for_user(user_id: str, body: SqlSnippetCreateRequest) -> dict:
    normalized = validate_readonly_sql(body.sql_text)
    tags = normalize_snippet_tags(body.tags)
    sql = """
        insert into sql_snippets (project_id, author_user_id, title, sql_text, tags, updated_at)
        select %s::uuid, %s::uuid, %s, %s, %s::text[], now()
        where exists (
            select 1
            from projects p
            join workspace_members wm on wm.workspace_id = p.workspace_id
            where p.id = %s::uuid
              and wm.user_id = %s::uuid
              and wm.role in ('owner', 'editor')
        )
        returning
            id::text,
            project_id::text,
            author_user_id::text,
            title,
            sql_text,
            tags,
            is_pinned,
            pinned_at::text,
            created_at::text,
            updated_at::text
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    body.project_id,
                    user_id,
                    body.title,
                    normalized,
                    tags,
                    body.project_id,
                    user_id,
                ),
            )
            row = cur.fetchone()
    if not row:
        raise PermissionError("Not allowed to create snippet for this project")
    return {
        "id": row[0],
        "project_id": row[1],
        "author_user_id": row[2],
        "title": row[3],
        "sql_text": row[4],
        "tags": row[5] or [],
        "is_pinned": bool(row[6]),
        "pinned_at": row[7],
        "created_at": row[8],
        "updated_at": row[9],
    }


def delete_snippet_for_user(user_id: str, snippet_id: str) -> None:
    sql = """
        delete from sql_snippets s
        using projects p, workspace_members wm
        where s.id = %s::uuid
          and p.id = s.project_id
          and wm.workspace_id = p.workspace_id
          and wm.user_id = %s::uuid
          and (
            s.author_user_id = %s::uuid
            or wm.role in ('owner', 'editor')
          )
    """
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (snippet_id, user_id, user_id))
            if cur.rowcount <= 0:
                raise PermissionError("Snippet not found or not allowed to delete")


def update_snippet_for_user(
    user_id: str,
    snippet_id: str,
    body: SqlSnippetUpdateRequest,
) -> dict:
    fields = []
    params: list = []
    if body.title is not None:
        fields.append("title = %s")
        params.append(body.title)
    if body.sql_text is not None:
        normalized = validate_readonly_sql(body.sql_text)
        fields.append("sql_text = %s")
        params.append(normalized)
    if body.tags is not None:
        tags = normalize_snippet_tags(body.tags)
        fields.append("tags = %s::text[]")
        params.append(tags)
    if body.is_pinned is not None:
        fields.append("is_pinned = %s")
        params.append(bool(body.is_pinned))
        fields.append("pinned_at = case when %s then now() else null end")
        params.append(bool(body.is_pinned))
    fields.append("updated_at = now()")

    if len(fields) <= 1:
        raise ValueError("No fields to update")

    sql = f"""
        update sql_snippets s
        set {", ".join(fields)}
        from projects p, workspace_members wm
        where s.id = %s::uuid
          and p.id = s.project_id
          and wm.workspace_id = p.workspace_id
          and wm.user_id = %s::uuid
          and (
            s.author_user_id = %s::uuid
            or wm.role in ('owner', 'editor')
          )
        returning
            s.id::text,
            s.project_id::text,
            s.author_user_id::text,
            s.title,
            s.sql_text,
            s.tags,
            s.is_pinned,
            s.pinned_at::text,
            s.created_at::text,
            s.updated_at::text
    """
    params.extend([snippet_id, user_id, user_id])

    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            row = cur.fetchone()
    if not row:
        raise PermissionError("Snippet not found or not allowed to update")
    return {
        "id": row[0],
        "project_id": row[1],
        "author_user_id": row[2],
        "title": row[3],
        "sql_text": row[4],
        "tags": row[5] or [],
        "is_pinned": bool(row[6]),
        "pinned_at": row[7],
        "created_at": row[8],
        "updated_at": row[9],
    }
