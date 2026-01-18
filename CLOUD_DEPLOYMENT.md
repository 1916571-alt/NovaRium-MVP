# NovaRium Cloud Deployment Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLOUD DEPLOYMENT                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐          ┌─────────────────┐                │
│  │  Streamlit Cloud │ ◄─────► │   Render.com    │                │
│  │  (Admin Dashboard)│  HTTP   │   (FastAPI)     │                │
│  │  Port: 8501      │         │   Port: 8000    │                │
│  └────────┬─────────┘         └────────┬────────┘                │
│           │                            │                          │
│           └────────────┬───────────────┘                          │
│                        ▼                                          │
│              ┌─────────────────┐                                  │
│              │    Supabase     │                                  │
│              │   (PostgreSQL)  │                                  │
│              │   Free Tier     │                                  │
│              └─────────────────┘                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. GitHub account (for code hosting)
2. Supabase account (free tier: https://supabase.com)
3. Render.com account (free tier: https://render.com)
4. Streamlit Cloud account (free tier: https://streamlit.io/cloud)

---

## Step 1: Setup Supabase Database

### 1.1 Create Project
1. Go to https://supabase.com and create a new project
2. Note down your project reference (e.g., `abcdefghijkl`)
3. Set a strong database password

### 1.2 Get Connection Details
Navigate to **Project Settings > Database**:
- **Connection string (URI)**:
  ```
  postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
  ```

Navigate to **Project Settings > API**:
- **Project URL**: `https://[PROJECT-REF].supabase.co`
- **anon public key**: `eyJhbGci...`

### 1.3 Initialize Schema (Optional)
Run this SQL in Supabase SQL Editor to pre-create tables:

```sql
-- Events table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255),
    user_id VARCHAR(255),
    event_name VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    value DOUBLE PRECISION DEFAULT 0,
    run_id VARCHAR(255)
);

-- Assignments table
CREATE TABLE IF NOT EXISTS assignments (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    experiment_id VARCHAR(255),
    variant VARCHAR(10),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    run_id VARCHAR(255),
    weight FLOAT DEFAULT 1.0
);

-- Experiments table
CREATE TABLE IF NOT EXISTS experiments (
    exp_id SERIAL PRIMARY KEY,
    target VARCHAR(255),
    hypothesis TEXT,
    primary_metric VARCHAR(100),
    guardrails VARCHAR(500),
    sample_size INTEGER,
    start_date DATE,
    end_date DATE,
    traffic_split FLOAT,
    p_value FLOAT,
    decision VARCHAR(50),
    learning_note TEXT,
    run_id VARCHAR(255),
    control_rate FLOAT,
    test_rate FLOAT,
    lift FLOAT,
    guardrail_results TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Adoptions table
CREATE TABLE IF NOT EXISTS adoptions (
    adoption_id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(255),
    variant_config TEXT,
    adopted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_events_run_id ON events(run_id);
CREATE INDEX IF NOT EXISTS idx_assignments_run_id ON assignments(run_id);
```

---

## Step 2: Deploy FastAPI to Render

### 2.1 Push Code to GitHub
```bash
git add .
git commit -m "Add cloud deployment configuration"
git push origin main
```

### 2.2 Create Render Web Service
1. Go to https://dashboard.render.com
2. Click **New > Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `novarium-api`
   - **Region**: Oregon (or nearest)
   - **Branch**: `main`
   - **Root Directory**: (leave empty)
   - **Runtime**: Docker
   - **Plan**: Free

### 2.3 Set Environment Variables
In Render Dashboard > Environment:

| Key | Value |
|-----|-------|
| `DB_MODE` | `supabase` |
| `DATABASE_URL` | `postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres` |
| `SUPABASE_URL` | `https://[PROJECT].supabase.co` |
| `SUPABASE_KEY` | `your-anon-key` |
| `ALLOWED_ORIGINS` | `*` (or your Streamlit URL) |

### 2.4 Deploy
Click **Deploy** and wait for build to complete.
Your API will be available at: `https://novarium-api.onrender.com`

---

## Step 3: Deploy Streamlit to Streamlit Cloud

### 3.1 Connect Repository
1. Go to https://share.streamlit.io
2. Click **New app**
3. Select your GitHub repository
4. Configure:
   - **Main file path**: `src/app.py`
   - **Branch**: `main`

### 3.2 Set Secrets
In Streamlit Cloud > App Settings > Secrets, add:

```toml
DB_MODE = "supabase"
DATABASE_URL = "postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"
SUPABASE_URL = "https://[PROJECT].supabase.co"
SUPABASE_KEY = "your-anon-key"
TARGET_APP_URL = "https://novarium-api.onrender.com"
```

### 3.3 Deploy
Click **Deploy** and wait for the app to start.

---

## Local Development

For local development, continue using DuckDB (no changes needed):

```bash
# No environment variables needed - defaults to DuckDB mode
streamlit run src/app.py
uvicorn target_app.main:app --reload
```

To test cloud mode locally:
```bash
# Copy .env.example to .env and fill in Supabase credentials
cp .env.example .env
# Edit .env with your Supabase details
# Set DB_MODE=supabase

# Then run normally
streamlit run src/app.py
```

---

## Troubleshooting

### Database Connection Errors
- Verify `DATABASE_URL` format is correct
- Check Supabase project is active (free tier pauses after inactivity)
- Ensure password doesn't contain special URL characters

### CORS Errors
- Add your Streamlit Cloud URL to `ALLOWED_ORIGINS`
- Format: `https://your-app.streamlit.app`

### Render Free Tier Limitations
- Apps sleep after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds
- 750 hours/month limit

### Streamlit Cloud Limitations
- Apps sleep after inactivity
- 1GB memory limit
- Private repos require paid plan

---

## Migration from Local to Cloud

To migrate existing local data to Supabase:

```python
# Run this script locally with both DBs accessible
from src.data.supabase_db import migrate_duckdb_to_supabase
migrate_duckdb_to_supabase()
```

---

## Cost Summary (Free Tier)

| Service | Free Tier Limits |
|---------|------------------|
| Supabase | 500MB database, 2GB bandwidth |
| Render | 750 hours/month, sleeps after 15min |
| Streamlit Cloud | 1GB memory, public repos only |

Total monthly cost: **$0** (within free tier limits)
