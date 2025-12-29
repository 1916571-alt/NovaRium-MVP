"""
NovaRium Database Schema v2.0

This module defines the database schema for both DuckDB (local) and PostgreSQL (Supabase).
Includes authentication tables, business data, and experiment tracking.
"""

# =========================================================
# Schema Definitions
# =========================================================

# Auth tables (shared between DuckDB and PostgreSQL)
AUTH_SCHEMA_DUCKDB = """
-- =========================================================
-- Authentication & User Management (DuckDB)
-- =========================================================

-- Platform Users (analysts, admins who use NovaRium)
CREATE TABLE IF NOT EXISTS auth_users (
    id VARCHAR PRIMARY KEY,  -- UUID as string
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),  -- NULL if OAuth only
    name VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500),
    role VARCHAR(20) NOT NULL DEFAULT 'analyst',  -- 'admin', 'analyst', 'viewer'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

-- OAuth Accounts (social login connections)
CREATE TABLE IF NOT EXISTS oauth_accounts (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    provider VARCHAR(50) NOT NULL,  -- 'google', 'github', 'kakao', 'naver'
    provider_user_id VARCHAR(255) NOT NULL,
    provider_email VARCHAR(255),
    access_token VARCHAR,
    refresh_token VARCHAR,
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES auth_users(id) ON DELETE CASCADE
);

-- Sessions (token-based authentication)
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES auth_users(id) ON DELETE CASCADE
);
"""

AUTH_SCHEMA_POSTGRES = """
-- =========================================================
-- Authentication & User Management (PostgreSQL)
-- =========================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Platform Users
CREATE TABLE IF NOT EXISTS auth_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    name VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500),
    role VARCHAR(20) NOT NULL DEFAULT 'analyst',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    CONSTRAINT chk_role CHECK (role IN ('admin', 'analyst', 'viewer'))
);

-- OAuth Accounts
CREATE TABLE IF NOT EXISTS oauth_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    provider_email VARCHAR(255),
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_oauth_provider_user UNIQUE (provider, provider_user_id)
);

-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(email);
CREATE INDEX IF NOT EXISTS idx_oauth_accounts_user_id ON oauth_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_oauth_accounts_provider ON oauth_accounts(provider, provider_user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
"""

# Warehouse schema (customers, orders)
WAREHOUSE_SCHEMA_DUCKDB = """
-- =========================================================
-- Warehouse DB: Business Data (DuckDB)
-- =========================================================

-- Customers (A/B test subjects, renamed from 'users')
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(10),
    age INTEGER,
    job VARCHAR(200),
    segment VARCHAR(50),
    joined_at TIMESTAMP NOT NULL,
    created_by VARCHAR,  -- FK to auth_users
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR PRIMARY KEY,
    customer_id VARCHAR NOT NULL,
    order_at TIMESTAMP NOT NULL,
    menu_item VARCHAR(100) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    created_by VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);
"""

WAREHOUSE_SCHEMA_POSTGRES = """
-- =========================================================
-- Warehouse DB: Business Data (PostgreSQL)
-- =========================================================

-- Customers
CREATE TABLE IF NOT EXISTS customers (
    customer_id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(10),
    age INTEGER CHECK (age >= 0 AND age <= 150),
    job VARCHAR(200),
    segment VARCHAR(50),
    joined_at TIMESTAMP NOT NULL,
    created_by UUID REFERENCES auth_users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    order_id UUID PRIMARY KEY,
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    order_at TIMESTAMP NOT NULL,
    menu_item VARCHAR(100) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount >= 0),
    created_by UUID REFERENCES auth_users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(segment);
CREATE INDEX IF NOT EXISTS idx_customers_joined_at ON customers(joined_at);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_at ON orders(order_at);
"""

# Experiment schema
EXPERIMENT_SCHEMA_DUCKDB = """
-- =========================================================
-- Experiment DB: A/B Test Data (DuckDB)
-- =========================================================

-- Experiments metadata
CREATE SEQUENCE IF NOT EXISTS exp_id_seq START 1;
CREATE TABLE IF NOT EXISTS experiments (
    exp_id INTEGER DEFAULT nextval('exp_id_seq'),
    name VARCHAR(100),
    target VARCHAR(255),
    hypothesis VARCHAR,
    description VARCHAR,
    primary_metric VARCHAR(100),
    guardrails VARCHAR,
    sample_size INTEGER,
    traffic_split FLOAT DEFAULT 0.5,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'draft',
    p_value FLOAT,
    control_rate FLOAT,
    test_rate FLOAT,
    lift FLOAT,
    decision VARCHAR(50),
    learning_note VARCHAR,
    guardrail_results VARCHAR,
    run_id VARCHAR(255),
    created_by VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assignments
CREATE TABLE IF NOT EXISTS assignments (
    id VARCHAR,
    user_id VARCHAR NOT NULL,  -- customer_id from target app
    experiment_id VARCHAR NOT NULL,
    variant VARCHAR(10) NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    run_id VARCHAR(255),
    weight FLOAT DEFAULT 1.0
);

-- Events
CREATE TABLE IF NOT EXISTS events (
    event_id VARCHAR,
    user_id VARCHAR NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    value DOUBLE DEFAULT 0,
    run_id VARCHAR(255),
    metadata VARCHAR  -- JSON string for DuckDB
);

-- Adoptions
CREATE TABLE IF NOT EXISTS adoptions (
    adoption_id INTEGER PRIMARY KEY,
    experiment_id VARCHAR NOT NULL,
    winning_variant VARCHAR(10),
    variant_config VARCHAR,
    adopted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    adopted_by VARCHAR,
    notes VARCHAR
);

-- Active Experiment (singleton)
CREATE TABLE IF NOT EXISTS active_experiment (
    id INTEGER PRIMARY KEY,
    is_active BOOLEAN DEFAULT FALSE,
    experiment_id VARCHAR,
    started_at TIMESTAMP
);
"""

EXPERIMENT_SCHEMA_POSTGRES = """
-- =========================================================
-- Experiment DB: A/B Test Data (PostgreSQL)
-- =========================================================

-- Experiments
CREATE TABLE IF NOT EXISTS experiments (
    exp_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100),
    target VARCHAR(255) NOT NULL,
    hypothesis TEXT,
    description TEXT,
    primary_metric VARCHAR(100) NOT NULL,
    guardrails TEXT,
    sample_size INTEGER,
    traffic_split FLOAT NOT NULL DEFAULT 0.5,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    p_value FLOAT,
    control_rate FLOAT,
    test_rate FLOAT,
    lift FLOAT,
    decision VARCHAR(50),
    learning_note TEXT,
    guardrail_results TEXT,
    run_id VARCHAR(255),
    created_by UUID REFERENCES auth_users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_exp_status CHECK (status IN ('draft', 'running', 'completed', 'archived')),
    CONSTRAINT chk_traffic_split CHECK (traffic_split >= 0 AND traffic_split <= 1)
);

-- Assignments
CREATE TABLE IF NOT EXISTS assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    experiment_id VARCHAR(255) NOT NULL,
    variant VARCHAR(10) NOT NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    run_id VARCHAR(255),
    weight FLOAT NOT NULL DEFAULT 1.0,
    CONSTRAINT uq_assignment UNIQUE (user_id, experiment_id, run_id)
);

-- Events
CREATE TABLE IF NOT EXISTS events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    value DOUBLE PRECISION DEFAULT 0,
    run_id VARCHAR(255),
    metadata JSONB
);

-- Adoptions
CREATE TABLE IF NOT EXISTS adoptions (
    adoption_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id VARCHAR(255) NOT NULL,
    winning_variant VARCHAR(10) NOT NULL,
    variant_config TEXT,
    adopted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    adopted_by UUID REFERENCES auth_users(id),
    notes TEXT
);

-- Active Experiment
CREATE TABLE IF NOT EXISTS active_experiment (
    id INTEGER PRIMARY KEY DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    experiment_id UUID,
    started_at TIMESTAMP,
    CONSTRAINT single_row CHECK (id = 1)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
CREATE INDEX IF NOT EXISTS idx_experiments_run_id ON experiments(run_id);
CREATE INDEX IF NOT EXISTS idx_assignments_experiment ON assignments(experiment_id);
CREATE INDEX IF NOT EXISTS idx_assignments_run_id ON assignments(run_id);
CREATE INDEX IF NOT EXISTS idx_assignments_user ON assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_name ON events(event_name);
CREATE INDEX IF NOT EXISTS idx_events_run_id ON events(run_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
"""

# =========================================================
# Migration Scripts
# =========================================================

MIGRATION_V2_DUCKDB = """
-- =========================================================
-- Migration: v1.0 → v2.0 (DuckDB)
-- Run this to upgrade existing databases
-- =========================================================

-- Phase 1: Create auth tables
{auth_schema}

-- Phase 2: Rename users → customers (if users table exists)
-- Note: DuckDB doesn't support ALTER TABLE RENAME, so we need to:
-- 1. Create new table
-- 2. Copy data
-- 3. Drop old table

-- Check if migration needed
-- If 'users' table exists and 'customers' doesn't:
CREATE TABLE IF NOT EXISTS customers AS
SELECT
    user_id AS customer_id,
    name,
    gender,
    age,
    job,
    segment,
    joined_at,
    NULL AS created_by,
    CURRENT_TIMESTAMP AS created_at
FROM users
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users')
  AND NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'customers');

-- Phase 3: Update orders table to reference customer_id
-- Add created_by column if not exists (DuckDB doesn't support IF NOT EXISTS for columns)
-- This needs to be done manually with ALTER TABLE ADD COLUMN

-- Phase 4: Add created_by to experiments if not exists
-- ALTER TABLE experiments ADD COLUMN IF NOT EXISTS created_by VARCHAR;
""".format(auth_schema=AUTH_SCHEMA_DUCKDB)

MIGRATION_V2_POSTGRES = """
-- =========================================================
-- Migration: v1.0 → v2.0 (PostgreSQL)
-- Run this to upgrade existing Supabase databases
-- =========================================================

-- Phase 1: Create auth tables
{auth_schema}

-- Phase 2: Rename users → customers
DO $$
BEGIN
    -- Check if users table exists and customers doesn't
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users' AND table_schema = 'public')
       AND NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'customers' AND table_schema = 'public')
    THEN
        -- Rename table
        ALTER TABLE users RENAME TO customers;
        -- Rename column
        ALTER TABLE customers RENAME COLUMN user_id TO customer_id;
        -- Add new columns
        ALTER TABLE customers ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES auth_users(id);
        ALTER TABLE customers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Phase 3: Update orders foreign key
DO $$
BEGIN
    -- Add created_by to orders if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'orders' AND column_name = 'created_by')
    THEN
        ALTER TABLE orders ADD COLUMN created_by UUID REFERENCES auth_users(id);
    END IF;

    -- Rename user_id to customer_id if needed
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'orders' AND column_name = 'user_id')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'orders' AND column_name = 'customer_id')
    THEN
        ALTER TABLE orders RENAME COLUMN user_id TO customer_id;
    END IF;
END $$;

-- Phase 4: Update experiments table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'experiments' AND column_name = 'created_by')
    THEN
        ALTER TABLE experiments ADD COLUMN created_by UUID REFERENCES auth_users(id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'experiments' AND column_name = 'name')
    THEN
        ALTER TABLE experiments ADD COLUMN name VARCHAR(100);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'experiments' AND column_name = 'description')
    THEN
        ALTER TABLE experiments ADD COLUMN description TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'experiments' AND column_name = 'status')
    THEN
        ALTER TABLE experiments ADD COLUMN status VARCHAR(20) DEFAULT 'draft';
    END IF;
END $$;

-- Phase 5: Update adoptions table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'adoptions' AND column_name = 'adopted_by')
    THEN
        ALTER TABLE adoptions ADD COLUMN adopted_by UUID REFERENCES auth_users(id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'adoptions' AND column_name = 'winning_variant')
    THEN
        ALTER TABLE adoptions ADD COLUMN winning_variant VARCHAR(10);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'adoptions' AND column_name = 'notes')
    THEN
        ALTER TABLE adoptions ADD COLUMN notes TEXT;
    END IF;
END $$;

-- Create indexes for new tables
{experiment_schema_indexes}
""".format(
    auth_schema=AUTH_SCHEMA_POSTGRES,
    experiment_schema_indexes="""
CREATE INDEX IF NOT EXISTS idx_experiments_created_by ON experiments(created_by);
CREATE INDEX IF NOT EXISTS idx_adoptions_experiment ON adoptions(experiment_id);
"""
)


# =========================================================
# Helper Functions
# =========================================================

def get_full_schema_duckdb() -> str:
    """Get complete DuckDB schema for fresh installation."""
    return "\n\n".join([
        AUTH_SCHEMA_DUCKDB,
        WAREHOUSE_SCHEMA_DUCKDB,
        EXPERIMENT_SCHEMA_DUCKDB
    ])


def get_full_schema_postgres() -> str:
    """Get complete PostgreSQL schema for fresh installation."""
    return "\n\n".join([
        AUTH_SCHEMA_POSTGRES,
        WAREHOUSE_SCHEMA_POSTGRES,
        EXPERIMENT_SCHEMA_POSTGRES
    ])


def get_migration_script(db_type: str = 'postgres') -> str:
    """Get migration script for upgrading from v1 to v2."""
    if db_type == 'postgres':
        return MIGRATION_V2_POSTGRES
    return MIGRATION_V2_DUCKDB


# =========================================================
# Schema Application Functions
# =========================================================

def apply_auth_schema_duckdb(con):
    """Apply auth schema to DuckDB connection."""
    statements = AUTH_SCHEMA_DUCKDB.split(';')
    for stmt in statements:
        stmt = stmt.strip()
        if stmt and not stmt.startswith('--'):
            try:
                con.execute(stmt)
            except Exception as e:
                print(f"Warning: {e}")


def apply_auth_schema_postgres(conn):
    """Apply auth schema to PostgreSQL connection."""
    try:
        with conn.cursor() as cur:
            cur.execute(AUTH_SCHEMA_POSTGRES)
        conn.commit()
        print("Auth schema applied to PostgreSQL")
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error applying auth schema: {e}")
        return False


if __name__ == "__main__":
    # Print schemas for review
    print("=" * 60)
    print("NovaRium Schema v2.0")
    print("=" * 60)
    print("\n### DuckDB Full Schema ###")
    print(get_full_schema_duckdb())
    print("\n### PostgreSQL Full Schema ###")
    print(get_full_schema_postgres())
