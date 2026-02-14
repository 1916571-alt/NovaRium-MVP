from contextlib import contextmanager

import psycopg2

from apps.api.core.config import settings


@contextmanager
def get_db_conn(user_id: str | None = None):
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is missing")
    conn = psycopg2.connect(settings.database_url)
    try:
        if user_id:
            with conn.cursor() as cur:
                # Make JWT subject available to PostgreSQL RLS policies.
                cur.execute(
                    "select set_config('request.jwt.claim.sub', %s, true)",
                    (user_id,),
                )
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
