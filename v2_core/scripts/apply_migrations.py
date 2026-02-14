from pathlib import Path

from apps.api.db.session import get_db_conn


def apply_all() -> None:
    migrations_dir = Path(__file__).resolve().parents[1] / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("No migration files found.")
        return

    print(f"Applying {len(migration_files)} migration files...")
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            for migration_file in migration_files:
                sql = migration_file.read_text(encoding="utf-8")
                print(f"- {migration_file.name}")
                cur.execute(sql)
    print("Done.")


if __name__ == "__main__":
    apply_all()

