import duckdb

con = duckdb.connect('novarium_local.db')

# Create adoptions table
con.execute("""
    CREATE TABLE IF NOT EXISTS adoptions (
        experiment_id VARCHAR,
        variant_config VARCHAR,
        adopted_at TIMESTAMP,
        lift FLOAT,
        p_value FLOAT
    )
""")

print("Adoptions table created successfully")

# Verify
tables = con.execute("SHOW TABLES").fetchall()
print(f"\nAll tables: {[t[0] for t in tables]}")

con.close()
