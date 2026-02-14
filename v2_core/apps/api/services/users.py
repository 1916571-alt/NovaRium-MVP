from apps.api.db.session import get_db_conn


def ensure_app_user(user_id: str, email: str | None = None) -> None:
    sql = """
        insert into users (id, email)
        values (%s::uuid, %s)
        on conflict (id) do update
        set email = coalesce(excluded.email, users.email)
    """
    fallback_email = email or f"{user_id}@local.invalid"
    with get_db_conn(user_id=user_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, fallback_email))

