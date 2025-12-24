import duckdb
import os

# Constants
# Constants
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'novarium_local.db')
RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'raw_data')

def initialize_db():
    print(f"Connecting to DuckDB at {DB_PATH}...")
    con = duckdb.connect(DB_PATH)
    return con

def load_data(con):
    # 1. Load basic CSVs (users, orders) for Overview context
    tables = ['users', 'orders']
    for table_name in tables:
        csv_path = os.path.join(RAW_DATA_DIR, f'{table_name}.csv')
        if os.path.exists(csv_path):
            print(f"Loading {table_name} from {csv_path}...")
            con.execute(f"DROP TABLE IF EXISTS {table_name}")
            con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_path}')")
        else:
            print(f"Warning: {csv_path} not found. (Run generating_data.py first if needed)")

    # 2. Educational Workflow Tables
    print("Creating 'assignments' table...")
    con.execute("DROP TABLE IF EXISTS assignments")
    con.execute("""
        CREATE TABLE assignments (
            user_id VARCHAR,
            experiment_id VARCHAR,
            variant VARCHAR,
            assigned_at TIMESTAMP,
            run_id VARCHAR,
            weight FLOAT DEFAULT 1.0
        )
    """)

    print("Creating 'events' table...")
    con.execute("DROP TABLE IF EXISTS events")
    con.execute("""
        CREATE TABLE events (
            event_id VARCHAR,
            user_id VARCHAR,
            event_name VARCHAR,
            timestamp TIMESTAMP,
            value DOUBLE,
            run_id VARCHAR
        )
    """)
    
    # 3. Experiment Retrospective (Updated Schema)
    print("Creating 'experiments' table (Retrospective)...")
    con.execute("DROP TABLE IF EXISTS experiments")
    con.execute("CREATE SEQUENCE IF NOT EXISTS exp_id_seq START 1")
    con.execute("""
        CREATE TABLE experiments (
            exp_id INTEGER DEFAULT nextval('exp_id_seq'),
            target VARCHAR,
            hypothesis VARCHAR,
            primary_metric VARCHAR,
            guardrails VARCHAR,
            sample_size INTEGER,
            start_date DATE,
            end_date DATE,
            traffic_split FLOAT,
            p_value FLOAT,
            decision VARCHAR,
            learning_note VARCHAR,
            run_id VARCHAR,
            control_rate FLOAT,
            test_rate FLOAT,
            lift FLOAT,
            guardrail_results VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("Schema setup complete.")

def verify_data(con):
    print("\nVerifying schema...")
    tables = ['users', 'orders', 'assignments', 'events', 'experiments']
    
    for table_name in tables:
        try:
            result = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            count = result[0]
            print(f"Table '{table_name}': {count} rows")
        except Exception as e:
            print(f"Table '{table_name}' check failed: {e}")

if __name__ == "__main__":
    con = initialize_db()
    load_data(con)
    verify_data(con)
    con.close()
    print("Warehouse setup complete.")
