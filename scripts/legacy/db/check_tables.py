import duckdb

con = duckdb.connect('novarium_local.db')

print("=== All Tables ===")
tables = con.execute("SHOW TABLES").fetchall()
for table in tables:
    print(f"  - {table[0]}")

print("\n=== Checking experiments table ===")
try:
    result = con.execute("SELECT COUNT(*) FROM experiments").fetchone()
    print(f"Experiments count: {result[0]}")

    if result[0] > 0:
        print("\nRecent experiments:")
        experiments = con.execute("SELECT hypothesis, decision, created_at FROM experiments ORDER BY created_at DESC LIMIT 3").fetchall()
        for exp in experiments:
            print(f"  - {exp[0]} | {exp[1]} | {exp[2]}")
except Exception as e:
    print(f"No experiments table or error: {e}")

print("\n=== Checking adoptions table ===")
try:
    result = con.execute("SELECT COUNT(*) FROM adoptions").fetchone()
    print(f"Adoptions count: {result[0]}")

    if result[0] > 0:
        print("\nAdoptions:")
        adoptions = con.execute("SELECT * FROM adoptions").fetchall()
        for adp in adoptions:
            print(f"  - {adp}")
except Exception as e:
    print(f"No adoptions table or error: {e}")

con.close()
