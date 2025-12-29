"""
NovaRium Database Abstraction Layer

Twelve-Factor App Compliant Database Module
- Factor III: Config - Store config in the environment
- Factor IV: Backing services - Treat backing services as attached resources
- Factor X: Dev/prod parity - Keep development, staging, and production as similar as possible

This module provides a unified interface for database operations,
automatically switching between DuckDB (local) and PostgreSQL (cloud)
based on environment configuration.

Usage:
    from src.data.database import db

    # Read data
    df = db.query("SELECT * FROM customers")

    # Write data
    db.execute("INSERT INTO events (user_id, event_name) VALUES (?, ?)", ["uid", "click"])

    # Batch operations
    db.batch([
        ("INSERT INTO events ...", [params1]),
        ("INSERT INTO events ...", [params2]),
    ])
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Dict, Any, Union
from contextlib import contextmanager
from enum import Enum

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Database")


# =========================================================
# Environment Configuration
# =========================================================

class Environment(Enum):
    """Application environment modes."""
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseType(Enum):
    """Supported database types."""
    DUCKDB = "duckdb"
    POSTGRES = "postgres"
    SUPABASE = "supabase"  # Alias for postgres


def _get_env(key: str, default: str = '') -> str:
    """
    Get environment variable with Streamlit secrets priority.
    Priority order:
    1. Streamlit secrets (st.secrets)
    2. OS environment variables
    3. Default value
    """
    # Try Streamlit secrets first (for Streamlit Cloud)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass

    return os.getenv(key, default)


def _load_dotenv():
    """Load .env file if available."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


# Load environment variables on import
_load_dotenv()


# =========================================================
# Configuration Class
# =========================================================

class DatabaseConfig:
    """
    Database configuration from environment variables.

    Environment Variables:
        ENV: Application environment (local/development/staging/production)
        DB_MODE: Database mode (duckdb/postgres/supabase)
        DATABASE_URL: PostgreSQL connection string
        TARGET_APP_URL: Target app URL for coordination
    """

    def __init__(self):
        self._refresh()

    def _refresh(self):
        """Refresh configuration from environment."""
        # Application environment
        env_str = _get_env('ENV', 'local').lower()
        self.environment = Environment(env_str) if env_str in [e.value for e in Environment] else Environment.LOCAL

        # Database mode
        db_mode = _get_env('DB_MODE', 'duckdb').lower()
        if db_mode in ['supabase', 'postgres', 'postgresql']:
            self.db_type = DatabaseType.POSTGRES
        else:
            self.db_type = DatabaseType.DUCKDB

        # Database URLs
        self._database_url = self._ensure_ssl(_get_env('DATABASE_URL', ''))

        # Paths for DuckDB
        self._base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._data_dir = os.path.join(self._base_dir, 'data')

        # Target App URL (for DuckDB coordination)
        self.target_app_url = _get_env('TARGET_APP_URL', 'http://localhost:8000')

    @staticmethod
    def _ensure_ssl(url: str) -> str:
        """Add sslmode=require for cloud PostgreSQL connections."""
        if not url:
            return url
        if 'sslmode=' not in url:
            separator = '&' if '?' in url else '?'
            return f"{url}{separator}sslmode=require"
        return url

    @property
    def database_url(self) -> str:
        return self._database_url

    @property
    def warehouse_db_path(self) -> str:
        return os.path.join(self._data_dir, 'db', 'novarium_warehouse.db')

    @property
    def experiment_db_path(self) -> str:
        return os.path.join(self._data_dir, 'db', 'novarium_experiment.db')

    @property
    def is_cloud(self) -> bool:
        """Check if running in cloud mode."""
        return self.db_type == DatabaseType.POSTGRES and bool(self._database_url)

    @property
    def is_local(self) -> bool:
        """Check if running in local mode."""
        return self.db_type == DatabaseType.DUCKDB

    def __repr__(self):
        return (
            f"DatabaseConfig(env={self.environment.value}, "
            f"db_type={self.db_type.value}, "
            f"is_cloud={self.is_cloud})"
        )


# Global configuration instance
config = DatabaseConfig()


# =========================================================
# Database Adapter Interface
# =========================================================

class DatabaseAdapter(ABC):
    """Abstract base class for database adapters."""

    @abstractmethod
    def query(self, sql: str, params: tuple = None, db_type: str = 'experiment') -> 'pd.DataFrame':
        """Execute SELECT query and return DataFrame."""
        pass

    @abstractmethod
    def execute(self, sql: str, params: tuple = None) -> Dict[str, Any]:
        """Execute write statement (INSERT/UPDATE/DELETE)."""
        pass

    @abstractmethod
    def batch(self, operations: List[Tuple[str, tuple]]) -> Dict[str, Any]:
        """Execute multiple write operations in a transaction."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check database connectivity."""
        pass

    @abstractmethod
    def close(self):
        """Close database connections."""
        pass


# =========================================================
# DuckDB Adapter
# =========================================================

class DuckDBAdapter(DatabaseAdapter):
    """DuckDB adapter for local development."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._warehouse_conn = None
        self._experiment_conn = None

    def _get_connection(self, db_type: str = 'experiment', read_only: bool = True):
        """Get DuckDB connection."""
        import duckdb

        if db_type == 'warehouse':
            db_path = self.config.warehouse_db_path
        else:
            db_path = self.config.experiment_db_path

        return duckdb.connect(db_path, read_only=read_only)

    def query(self, sql: str, params: tuple = None, db_type: str = 'experiment') -> 'pd.DataFrame':
        """Execute SELECT query."""
        import pandas as pd

        try:
            with self._get_connection(db_type, read_only=True) as conn:
                if params:
                    return conn.execute(sql, list(params)).df()
                return conn.execute(sql).df()
        except Exception as e:
            logger.error(f"DuckDB query error: {e}")
            return pd.DataFrame()

    def execute(self, sql: str, params: tuple = None) -> Dict[str, Any]:
        """Execute write statement with Target App coordination."""
        return self._coordinated_write([(sql, params)])[0] if self._coordinated_write([(sql, params)]) else {"status": "error"}

    def batch(self, operations: List[Tuple[str, tuple]]) -> Dict[str, Any]:
        """Execute batch operations with coordination."""
        return self._coordinated_write(operations)

    def _coordinated_write(self, operations: List[Tuple[str, tuple]]) -> Dict[str, Any]:
        """Write with Target App DB coordination."""
        import duckdb
        import requests
        import time

        results = []
        try:
            # Step 1: Request Target App to release DB
            try:
                requests.post(f"{self.config.target_app_url}/admin/db_release", timeout=5)
            except requests.exceptions.ConnectionError:
                pass  # Target App not running

            time.sleep(0.3)

            # Step 2: Execute operations
            with duckdb.connect(self.config.experiment_db_path) as conn:
                for sql, params in operations:
                    try:
                        if params:
                            conn.execute(sql, list(params) if params else None)
                        else:
                            conn.execute(sql)
                        results.append({"sql": sql[:50], "status": "success"})
                    except Exception as e:
                        results.append({"sql": sql[:50], "status": "error", "message": str(e)})

            # Step 3: Reconnect Target App
            try:
                requests.post(f"{self.config.target_app_url}/admin/db_reconnect", timeout=5)
            except:
                pass

            return {"status": "success", "results": results}

        except Exception as e:
            return {"status": "error", "message": str(e), "results": results}

    def health_check(self) -> Dict[str, Any]:
        """Check DuckDB connectivity."""
        import duckdb

        result = {"mode": "duckdb", "status": "unknown"}
        try:
            with duckdb.connect(self.config.experiment_db_path, read_only=True) as conn:
                conn.execute("SELECT 1")
            result["status"] = "connected"
            result["database"] = "DuckDB (Local)"
            result["paths"] = {
                "warehouse": self.config.warehouse_db_path,
                "experiment": self.config.experiment_db_path
            }
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def close(self):
        """Close connections."""
        pass  # DuckDB connections are managed per-query


# =========================================================
# PostgreSQL Adapter (Supabase)
# =========================================================

class PostgresAdapter(DatabaseAdapter):
    """PostgreSQL adapter for cloud deployment (Supabase)."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pool = None
        self._pool_error = None
        self._pool_last_attempt = 0
        self._RETRY_INTERVAL = 30

    def _get_pool(self, force_retry: bool = False):
        """Get or create connection pool with retry logic."""
        import time

        if not self.config.database_url:
            self._pool_error = "DATABASE_URL not set"
            return None

        if self._pool is not None:
            return self._pool

        # Throttle retry attempts
        current_time = time.time()
        if not force_retry and self._pool_last_attempt > 0:
            if current_time - self._pool_last_attempt < self._RETRY_INTERVAL:
                return None

        self._pool_last_attempt = current_time

        try:
            import psycopg2
            from psycopg2 import pool

            self._pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=self.config.database_url,
                connect_timeout=10
            )

            # Test connection
            test_conn = self._pool.getconn()
            try:
                with test_conn.cursor() as cur:
                    cur.execute("SELECT 1")
                logger.info("PostgreSQL connection pool created successfully")
                self._pool_error = None
            finally:
                self._pool.putconn(test_conn)

            return self._pool

        except Exception as e:
            self._pool_error = str(e)
            logger.error(f"PostgreSQL pool creation failed: {e}")
            self._pool = None
            return None

    @contextmanager
    def _get_connection(self):
        """Get connection from pool."""
        pool = self._get_pool()
        if pool is None:
            raise ConnectionError(f"PostgreSQL pool not available: {self._pool_error}")

        conn = None
        try:
            conn = pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn and pool:
                pool.putconn(conn)

    def query(self, sql: str, params: tuple = None, db_type: str = 'experiment') -> 'pd.DataFrame':
        """Execute SELECT query."""
        import pandas as pd

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Convert DuckDB placeholders to PostgreSQL
                    pg_sql = sql.replace('?', '%s')
                    cur.execute(pg_sql, params)
                    if cur.description:
                        columns = [desc[0] for desc in cur.description]
                        data = cur.fetchall()
                        return pd.DataFrame(data, columns=columns)
                    return pd.DataFrame()
        except Exception as e:
            logger.error(f"PostgreSQL query error: {e}")
            return pd.DataFrame()

    def execute(self, sql: str, params: tuple = None) -> Dict[str, Any]:
        """Execute write statement."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    pg_sql = sql.replace('?', '%s')
                    cur.execute(pg_sql, params)
            return {"status": "success", "message": "Write completed"}
        except Exception as e:
            logger.error(f"PostgreSQL write error: {e}")
            return {"status": "error", "message": str(e)}

    def batch(self, operations: List[Tuple[str, tuple]]) -> Dict[str, Any]:
        """Execute batch operations."""
        results = []
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    for sql, params in operations:
                        try:
                            pg_sql = sql.replace('?', '%s')
                            cur.execute(pg_sql, params)
                            results.append({"sql": sql[:50], "status": "success"})
                        except Exception as e:
                            results.append({"sql": sql[:50], "status": "error", "message": str(e)})
            return {"status": "success", "results": results}
        except Exception as e:
            return {"status": "error", "message": str(e), "results": results}

    def health_check(self) -> Dict[str, Any]:
        """Check PostgreSQL connectivity."""
        result = {"mode": "postgres", "status": "unknown"}
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            result["status"] = "connected"
            result["database"] = "PostgreSQL (Supabase)"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            if self._pool_error:
                result["pool_error"] = self._pool_error
        return result

    def close(self):
        """Close connection pool."""
        if self._pool:
            self._pool.closeall()
            self._pool = None
            logger.info("PostgreSQL connection pool closed")


# =========================================================
# Database Factory
# =========================================================

class Database:
    """
    Main database interface with automatic adapter selection.

    This class implements the Adapter pattern to provide a unified
    interface for both DuckDB and PostgreSQL databases.
    """

    _instance: Optional['Database'] = None

    def __new__(cls):
        """Singleton pattern for database instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.config = config
        self._adapter: Optional[DatabaseAdapter] = None
        self._initialized = True
        self._init_adapter()

    def _init_adapter(self):
        """Initialize the appropriate database adapter."""
        if self.config.is_cloud:
            logger.info(f"Initializing PostgreSQL adapter (cloud mode)")
            self._adapter = PostgresAdapter(self.config)
        else:
            logger.info(f"Initializing DuckDB adapter (local mode)")
            self._adapter = DuckDBAdapter(self.config)

    def reinitialize(self):
        """Reinitialize adapter (useful after config change)."""
        if self._adapter:
            self._adapter.close()
        self.config._refresh()
        self._init_adapter()

    @property
    def adapter(self) -> DatabaseAdapter:
        """Get current database adapter."""
        if self._adapter is None:
            self._init_adapter()
        return self._adapter

    # Delegate methods to adapter
    def query(self, sql: str, params: tuple = None, db_type: str = 'experiment') -> 'pd.DataFrame':
        """Execute SELECT query."""
        return self.adapter.query(sql, params, db_type)

    def execute(self, sql: str, params: tuple = None) -> Dict[str, Any]:
        """Execute write statement."""
        return self.adapter.execute(sql, params)

    def batch(self, operations: List[Tuple[str, tuple]]) -> Dict[str, Any]:
        """Execute batch operations."""
        return self.adapter.batch(operations)

    def health_check(self) -> Dict[str, Any]:
        """Check database connectivity."""
        return self.adapter.health_check()

    def close(self):
        """Close database connections."""
        if self._adapter:
            self._adapter.close()

    # Utility methods
    @property
    def is_cloud(self) -> bool:
        return self.config.is_cloud

    @property
    def is_local(self) -> bool:
        return self.config.is_local

    @property
    def db_type(self) -> str:
        return self.config.db_type.value

    def __repr__(self):
        return f"Database({self.config})"


# =========================================================
# Module-level Singleton Instance
# =========================================================

# Create singleton instance for easy import
db = Database()


# =========================================================
# Backward Compatibility Functions
# =========================================================

def run_query(sql: str, params: tuple = None, db_type: str = 'experiment') -> 'pd.DataFrame':
    """Backward compatible query function."""
    return db.query(sql, params, db_type)


def execute_write(sql: str, params: tuple = None) -> Dict[str, Any]:
    """Backward compatible write function."""
    return db.execute(sql, params)


def execute_batch(operations: List[Tuple[str, tuple]]) -> Dict[str, Any]:
    """Backward compatible batch function."""
    return db.batch(operations)


def health_check() -> Dict[str, Any]:
    """Backward compatible health check."""
    return db.health_check()


def is_cloud_mode() -> bool:
    """Check if running in cloud mode."""
    return db.is_cloud


# =========================================================
# CLI Testing
# =========================================================

if __name__ == "__main__":
    print("=" * 60)
    print("NovaRium Database Module")
    print("=" * 60)
    print(f"\nConfiguration: {config}")
    print(f"\nHealth Check: {db.health_check()}")
