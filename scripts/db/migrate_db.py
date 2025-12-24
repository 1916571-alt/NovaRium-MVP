"""
Database Migration Script - Add run_id columns
Migrates existing novarium_local.db to new schema with run_id support
"""
import duckdb
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'novarium_local.db')

def migrate():
    print(f"[>] Starting migration of {DB_PATH}...")

    if not os.path.exists(DB_PATH):
        print(f"[!] Database not found at {DB_PATH}")
        print("[*] Please run: python src/data/db.py first")
        return

    con = duckdb.connect(DB_PATH)

    try:
        # Check current schema
        print("[1] Checking current schema...")
        tables = con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()
        print(f"    Found tables: {[t[0] for t in tables]}")

        # Check if run_id already exists in assignments
        cols_assignments = con.execute("PRAGMA table_info('assignments')").fetchall()
        col_names_assignments = [c[1] for c in cols_assignments]

        if 'run_id' in col_names_assignments:
            print("[!] Migration already applied (run_id exists in assignments)")
            print("[*] Database is up to date!")
            con.close()
            return

        print("[2] Adding run_id column to assignments...")
        con.execute("ALTER TABLE assignments ADD COLUMN run_id VARCHAR")

        print("[3] Checking events table schema...")
        cols_events = con.execute("PRAGMA table_info('events')").fetchall()
        col_names_events = [c[1] for c in cols_events]

        if 'value' not in col_names_events:
            print("[4] Adding value column to events...")
            con.execute("ALTER TABLE events ADD COLUMN value DOUBLE")

        if 'run_id' not in col_names_events:
            print("[5] Adding run_id column to events...")
            con.execute("ALTER TABLE events ADD COLUMN run_id VARCHAR")

        print("[6] Updating experiments table...")
        cols_experiments = con.execute("PRAGMA table_info('experiments')").fetchall()
        col_names_experiments = [c[1] for c in cols_experiments]

        if 'run_id' not in col_names_experiments:
            con.execute("ALTER TABLE experiments ADD COLUMN run_id VARCHAR")
            con.execute("ALTER TABLE experiments ADD COLUMN control_rate FLOAT")
            con.execute("ALTER TABLE experiments ADD COLUMN test_rate FLOAT")
            con.execute("ALTER TABLE experiments ADD COLUMN lift FLOAT")
            con.execute("ALTER TABLE experiments ADD COLUMN guardrail_results VARCHAR")

        print("[7] Setting existing data run_id to NULL (treated as historical baseline)...")
        con.execute("UPDATE assignments SET run_id = NULL WHERE run_id IS NULL")
        con.execute("UPDATE events SET run_id = NULL WHERE run_id IS NULL")

        print("[✓] Migration completed successfully!")
        print("")
        print("Next steps:")
        print("  1. Restart target app: python target_app/main.py")
        print("  2. Restart streamlit: streamlit run src/app.py")
        print("  3. Run a new experiment to test run_id functionality")

    except Exception as e:
        print(f"[X] Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        con.close()

if __name__ == "__main__":
    migrate()
