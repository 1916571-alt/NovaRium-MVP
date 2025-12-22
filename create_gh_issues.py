import subprocess
import time

issues = [
    {
        "title": "Phase 1: Python Environment Setup",
        "body": "**Background**: We need a local environment to run the data generation scripts.\n\n**Details**: Install `faker`, `pandas`, `duckdb`, `scipy`.\n\n**Acceptance Criteria**: `pip freeze` shows all required libraries."
    },
    {
        "title": "Phase 1: Script Structure (generating_data.py)",
        "body": "**Background**: A single script will handle all data generation as per the 'Simple' objective.\n\n**Details**: Create `generating_data.py` with main execution block.\n\n**Acceptance Criteria**: Script runs without errors and prints a start message."
    },
    {
        "title": "Phase 1: User Data Logic (users.csv)",
        "body": "**Background**: We need approx 1,000 users to simulate a realistic user base.\n\n**Details**: Use `faker` to generate names, emails, signup dates.\n\n**Acceptance Criteria**: `raw_data/users.csv` exists with ~1,000 rows."
    },
    {
        "title": "Phase 1: Order Data Logic (orders.csv)",
        "body": "**Background**: Transaction data is needed for revenue and retention analysis.\n\n**Details**: Generate orders linked to user IDs with timestamps and amounts.\n\n**Acceptance Criteria**: `raw_data/orders.csv` exists and foreign keys match users."
    },
    {
        "title": "Phase 1: A/B Test Logs (ab_test_logs.csv)",
        "body": "**Background**: To demonstrate experimentation logic.\n\n**Details**: Assign users to 'control' or 'test' groups and simulate conversion events.\n\n**Acceptance Criteria**: `raw_data/ab_test_logs.csv` exists with group assignments."
    },
    {
        "title": "Phase 1: Verify CSV Output",
        "body": "**Background**: Ensure all data is ready for the Data Warehouse phase.\n\n**Details**: Check existence and non-emptiness of all files in `raw_data/`.\n\n**Acceptance Criteria**: All 3 CSV files are present and valid."
    },
    {
        "title": "Phase 2: DuckDB Loader Script",
        "body": "**Background**: We need to load CSVs into an OLAP database for analysis.\n\n**Details**: Write python code to connect to DuckDB and execute `COPY` or `INSERT`.\n\n**Acceptance Criteria**: Script connects to `novarium_local.db`."
    },
    {
        "title": "Phase 2: Database Initialization",
        "body": "**Background**: A clean database file is required.\n\n**Details**: Ensure `novarium_local.db` is created.\n\n**Acceptance Criteria**: DB file exists."
    },
    {
        "title": "Phase 2: Data Loading (users, orders, logs)",
        "body": "**Background**: Tables must mirror the raw data.\n\n**Details**: Create tables and load data from CSVs.\n\n**Acceptance Criteria**: `SELECT count(*)` matches CSV row counts."
    },
    {
        "title": "Phase 2: Schema Verification",
        "body": "**Background**: Ensure data types are correct for analysis (dates, floats).\n\n**Details**: Inspect table schemas.\n\n**Acceptance Criteria**: Schema columns match expected types."
    },
    {
        "title": "Phase 3: Analysis Script Setup (analysis.ipynb)",
        "body": "**Background**: The environment for deriving insights.\n\n**Details**: Create a Jupyter Notebook or Python script connecting to the DB.\n\n**Acceptance Criteria**: Notebook opens and connects to DB."
    },
    {
        "title": "Phase 3: Data Mart Construction",
        "body": "**Background**: Pre-aggregated tables speed up analysis.\n\n**Details**: Create `user_stats`, `daily_sales` views/tables.\n\n**Acceptance Criteria**: Tables exist and can be queried."
    },
    {
        "title": "Phase 3: Cohort Analysis (Retention)",
        "body": "**Background**: Verify 'Stickiness' of the service.\n\n**Details**: Calculate weekly retention rates.\n\n**Acceptance Criteria**: Retention heatmap or table produced."
    },
    {
        "title": "Phase 3: Segmentation Analysis",
        "body": "**Background**: Understand different user behaviors.\n\n**Details**: Compare metrics between segments (e.g., by job or age).\n\n**Acceptance Criteria**: Comparison chart/table produced."
    },
    {
        "title": "Phase 3: A/B Test Analysis",
        "body": "**Background**: Validate hypothesis using statistical significance.\n\n**Details**: Calculate CVR for Control vs Test and P-value.\n\n**Acceptance Criteria**: Statistical result (Significance boolean) output."
    },
    {
        "title": "Phase 3: ROI Calculation",
        "body": "**Background**: Demonstrate business acumen.\n\n**Details**: Aggregate total revenue and compare against simulated costs.\n\n**Acceptance Criteria**: Final ROI number produced."
    },
    {
        "title": "Phase 3: Final Report",
        "body": "**Background**: Communicate findings to stakeholders.\n\n**Details**: Summarize all findings in Markdown or Notebook.\n\n**Acceptance Criteria**: Final report file covers all key metrics."
    }
]

print(f"Starting creation of {len(issues)} issues...")

for i, issue in enumerate(issues):
    cmd = [
        "gh", "issue", "create",
        "--title", issue["title"],
        "--body", issue["body"]
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"[{i+1}/{len(issues)}] Created: {result.stdout.strip()}")
        time.sleep(1) # Simple rate limiting
    except subprocess.CalledProcessError as e:
        print(f"Failed to create issue '{issue['title']}': {e.stderr}")

print("Done.")
