import duckdb
import pandas as pd
from datetime import datetime
import os

# Config
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'novarium_local.db')

def run_etl():
    print(f"[{datetime.now()}] Starting ETL Process...")
    con = duckdb.connect(DB_PATH)
    
    try:
        # 1. Aggregate Daily Stats (Source -> Staging Logic)
        print("[-] Aggregating Logging Data...")
        query = """
        WITH daily_stats AS (
            SELECT 
                date_trunc('day', assigned_at) as report_date,
                COUNT(DISTINCT a.user_id) as total_users,
                COUNT(DISTINCT CASE WHEN e.event_name = 'click_banner' THEN e.user_id END) as click_count,
                COUNT(DISTINCT CASE WHEN e.event_name = 'purchase' THEN e.user_id END) as total_orders,
                COALESCE(SUM(CASE WHEN e.event_name = 'purchase' THEN e.value ELSE 0 END), 0) as total_revenue
            FROM assignments a
            LEFT JOIN events e ON a.user_id = e.user_id
            GROUP BY 1
        )
        SELECT 
            report_date,
            total_users,
            total_revenue,
            total_orders,
            click_count,
            (click_count::FLOAT / NULLIF(total_users, 0)) as ctr,
            (total_orders::FLOAT / NULLIF(click_count, 0)) as cvr,
            (total_revenue / NULLIF(total_orders, 0)) as aov,
            CURRENT_TIMESTAMP as updated_at
        FROM daily_stats
        WHERE report_date IS NOT NULL
        ORDER BY report_date ASC
        """
        
        df_kpi = con.execute(query).df()
        
        if df_kpi.empty:
            print("[!] No data found to aggregate.")
            return

        # 2. Load to Data Mart (Upsert)
        # DuckDB doesn't support generic UPSERT easily in old versions, but we can DELETE -> INSERT for simplicity in this MVP
        print(f"[-] Loading {len(df_kpi)} rows into Data Mart...")
        
        # Determine date range to replace
        min_date = df_kpi['report_date'].min()
        
        # Transactional Replace
        con.execute("BEGIN TRANSACTION")
        con.execute(f"DELETE FROM dm_daily_kpi WHERE report_date >= '{min_date}'")
        con.execute("INSERT INTO dm_daily_kpi SELECT * FROM df_kpi")
        con.execute("COMMIT")
        
        print(f"[+] ETL Success! {len(df_kpi)} days processed.")
        
        # Validation
        chk = con.execute("SELECT COUNT(*) FROM dm_daily_kpi").fetchone()[0]
        print(f"[*] Total rows in Mart: {chk}")
        
    except Exception as e:
        print(f"[X] ETL Failed: {e}")
        con.execute("ROLLBACK")
    finally:
        con.close()

if __name__ == "__main__":
    run_etl()
