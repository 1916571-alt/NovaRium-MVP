import duckdb
import random
from datetime import datetime, timedelta
import os
import pandas as pd
import numpy as np

# Config
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'novarium_local.db')
DAYS_HISTORY = 30
DAILY_USERS = 500  # Scale down slightly for speed

def generate_history():
    print(f"[>] Generating {DAYS_HISTORY} days of history...")
    con = duckdb.connect(DB_PATH)
    
    # Clean old history
    con.execute("DELETE FROM assignments WHERE user_id LIKE 'user_hist_%'")
    con.execute("DELETE FROM events WHERE user_id LIKE 'user_hist_%'")
    
    users = []
    events = []
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=DAYS_HISTORY)
    
    user_counter = 10000 # Start high to avoid collision with live sim
    
    for day in range(DAYS_HISTORY):
        current_date = start_date + timedelta(days=day)
        is_crisis = (DAYS_HISTORY - day) <= 3 # Last 3 days are CRISIS
        
        # Scenario Parameters
        # Normal: CTR 15%, CVR 20% (of clickers) -> Overall Conv ~3%
        # Crisis: CTR 4%, CVR 15% -> Overall Conv ~0.6% (Huge Drop)
        if is_crisis:
            ctr = 0.04
            cvr = 0.15
            traffic_vol = int(DAILY_USERS * 0.9) # Slight traffic dip too
            status = "[!] CRISIS"
        else:
            ctr = 0.15
            cvr = 0.20
            traffic_vol = DAILY_USERS + random.randint(-50, 50)
            status = "[OK] Normal"
            
        print(f"[{current_date.strftime('%Y-%m-%d')}] Generating {traffic_vol} users... ({status})")
        
        for _ in range(traffic_vol):
            user_counter += 1
            uid = f"user_hist_{user_counter}"
            
            # 1. Assignment (Just logging visit)
            # Use 'history_load' as experiment_id to distinguish
            visit_time = current_date + timedelta(seconds=random.randint(0, 86400))
            users.append((uid, 'history_load', 'A', visit_time))
            
            # 2. Click Event
            if random.random() < ctr:
                click_time = visit_time + timedelta(seconds=random.randint(2, 60))
                events.append((f'evt_click_{user_counter}', uid, 'click_banner', click_time))
                
                # 3. Order Event
                if random.random() < cvr:
                    order_time = click_time + timedelta(seconds=random.randint(30, 300))
                    events.append((f'evt_order_{user_counter}', uid, 'purchase', order_time))

    # Bulk Insert
    print("[+] Saving to DuckDB...")
    df_u = pd.DataFrame(users, columns=['uid', 'eid', 'var', 'ts'])
    df_e = pd.DataFrame(events, columns=['eid', 'uid', 'name', 'ts'])
    
    # We need to match schema:
    # assignments: user_id, experiment_id, variant, assigned_at
    # events: event_id, user_id, event_name, timestamp
    
    # Fix column names for insert
    # assignments
    con.execute("INSERT INTO assignments SELECT uid, eid, var, ts FROM df_u")
    
    # events (event_id is first arg in tuple)
    con.execute("INSERT INTO events SELECT eid, uid, name, ts FROM df_e")
    
    con.close()
    print("[*] History Generation Complete!")

if __name__ == "__main__":
    generate_history()
