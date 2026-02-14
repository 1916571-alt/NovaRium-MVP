"""
Database Migration Script - Add weight column for hybrid simulation
"""
import duckdb
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'novarium_local.db')

def migrate():
    print(f"[>] Starting hybrid simulation migration on {DB_PATH}...")

    if not os.path.exists(DB_PATH):
        print(f"[!] Database not found at {DB_PATH}")
        print("[*] Please run: python src/data/db.py first")
        return

    con = duckdb.connect(DB_PATH)

    try:
        # Check if weight column already exists
        print("[1] Checking assignments table schema...")
        cols_assignments = con.execute("PRAGMA table_info('assignments')").fetchall()
        col_names = [c[1] for c in cols_assignments]

        if 'weight' in col_names:
            print("[!] Migration already applied (weight column exists)")
            print("[*] Database is up to date!")
            con.close()
            return

        # Add weight column
        print("[2] Adding weight column to assignments...")
        con.execute("ALTER TABLE assignments ADD COLUMN weight FLOAT DEFAULT 1.0")

        # Update existing data to weight=1.0
        print("[3] Setting existing data weight to 1.0...")
        con.execute("UPDATE assignments SET weight = 1.0 WHERE weight IS NULL")

        print("[✓] Migration completed successfully!")
        print("")
        print("Next steps:")
        print("  1. Restart target app: python target_app/main.py")
        print("  2. Restart streamlit: streamlit run src/app.py")
        print("  3. Run experiment with hybrid simulation (Step 3)")

    except Exception as e:
        print(f"[X] Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        con.close()

if __name__ == "__main__":
    migrate()
