import duckdb

con = duckdb.connect('novarium_local.db')

# Assignments count
assignments_count = con.execute("SELECT COUNT(*) as cnt FROM assignments WHERE user_id LIKE 'agent_%'").fetchone()[0]
print(f"Assignments with agent_: {assignments_count}")

# Events count
events_count = con.execute("SELECT COUNT(*) as cnt FROM events WHERE user_id LIKE 'agent_%'").fetchone()[0]
print(f"Events with agent_: {events_count}")

# Total assignments
total_assignments = con.execute("SELECT COUNT(*) FROM assignments").fetchone()[0]
print(f"Total assignments: {total_assignments}")

# Recent agent IDs in events
print("\nRecent Events:")
for row in con.execute("SELECT timestamp, user_id, event_name FROM events WHERE user_id LIKE 'agent_%' ORDER BY timestamp DESC LIMIT 5").fetchall():
    print(f"  {row[0]} | {row[1]} | {row[2]}")

con.close()
