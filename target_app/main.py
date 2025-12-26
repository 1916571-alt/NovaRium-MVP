from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import duckdb
import os
from datetime import datetime
import hashlib
import uuid
import threading
import logging

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TargetApp")

app = FastAPI(
    title="NovaRium Target App (NovaEats)",
    description="A/B Testing Target Application",
    version="1.0.0"
)

# CORS Middleware Configuration for Cloud Deployment
# Allow Streamlit Cloud and local development
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ['*'] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Mount Static
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Database Configuration (DuckDB local or PostgreSQL cloud)
DB_MODE = os.getenv('DB_MODE', 'duckdb')
DATABASE_URL = os.getenv('DATABASE_URL', '')
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'db', 'novarium_experiment.db')

# Singleton DB Connection (DuckDB for local, PostgreSQL pool for cloud)
db_con = None
db_lock = threading.Lock()
pg_pool = None

def is_cloud_mode():
    """Check if running in cloud mode (Supabase)."""
    return DB_MODE == 'supabase' and bool(DATABASE_URL)

def get_pg_pool():
    """Get or create PostgreSQL connection pool."""
    global pg_pool
    if pg_pool is None and DATABASE_URL:
        try:
            import psycopg2
            from psycopg2 import pool
            pg_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=DATABASE_URL
            )
            logger.info("PostgreSQL connection pool created")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL pool: {e}")
    return pg_pool

@app.on_event("startup")
async def startup_event():
    global db_con
    try:
        if is_cloud_mode():
            # Cloud mode: Use PostgreSQL
            logger.info("Starting in CLOUD mode (PostgreSQL/Supabase)")
            pool = get_pg_pool()
            if pool:
                # Setup schema if needed
                conn = pool.getconn()
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS events (
                                id SERIAL PRIMARY KEY,
                                event_id VARCHAR(255),
                                user_id VARCHAR(255),
                                event_name VARCHAR(100),
                                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                value DOUBLE PRECISION DEFAULT 0,
                                run_id VARCHAR(255)
                            )
                        """)
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS assignments (
                                id SERIAL PRIMARY KEY,
                                user_id VARCHAR(255),
                                experiment_id VARCHAR(255),
                                variant VARCHAR(10),
                                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                run_id VARCHAR(255),
                                weight FLOAT DEFAULT 1.0
                            )
                        """)
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS adoptions (
                                adoption_id SERIAL PRIMARY KEY,
                                experiment_id VARCHAR(255),
                                variant_config TEXT,
                                adopted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                    conn.commit()
                finally:
                    pool.putconn(conn)
                logger.info("PostgreSQL tables checked/created")
        else:
            # Local mode: Use DuckDB
            logger.info(f"Starting in LOCAL mode (DuckDB at {DB_PATH})")
            db_con = duckdb.connect(DB_PATH)

            # Ensure tables exist
            with db_lock:
                db_con.execute("CREATE TABLE IF NOT EXISTS events (event_id VARCHAR, user_id VARCHAR, event_name VARCHAR, timestamp TIMESTAMP, value DOUBLE, run_id VARCHAR)")
                db_con.execute("CREATE TABLE IF NOT EXISTS assignments (user_id VARCHAR, experiment_id VARCHAR, variant VARCHAR, assigned_at TIMESTAMP, run_id VARCHAR, weight FLOAT DEFAULT 1.0)")

            logger.info("DuckDB Connected and Tables Checked")
    except Exception as e:
        logger.error(f"DB Startup Error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    global db_con, pg_pool
    if db_con:
        db_con.close()
        logger.info("DuckDB Connection Closed")
    if pg_pool:
        pg_pool.closeall()
        logger.info("PostgreSQL Pool Closed")

# Health Check Endpoint (required for Render deployment)
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    status = {"status": "healthy", "mode": DB_MODE}
    try:
        if is_cloud_mode():
            pool = get_pg_pool()
            if pool:
                conn = pool.getconn()
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1")
                    status["database"] = "postgresql"
                finally:
                    pool.putconn(conn)
        else:
            if db_con:
                db_con.execute("SELECT 1")
                status["database"] = "duckdb"
    except Exception as e:
        status["status"] = "unhealthy"
        status["error"] = str(e)
    return status

def log_event(uid, variant, event_name, value=0.0, run_id=None):
    """Log an event to the database (supports both DuckDB and PostgreSQL)."""
    global db_con

    try:
        eid = str(uuid.uuid4())
        print(f"[App] Logging Event: {event_name} by {uid} (Value: {value})")

        if is_cloud_mode():
            # PostgreSQL mode
            pool = get_pg_pool()
            if pool:
                conn = pool.getconn()
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO events (event_id, user_id, event_name, timestamp, value, run_id) VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s, %s)",
                            (eid, uid, event_name, value, run_id)
                        )
                    conn.commit()
                finally:
                    pool.putconn(conn)
        else:
            # DuckDB mode
            if not db_con:
                logger.error("DB Not Connected")
                return
            with db_lock:
                db_con.execute("INSERT INTO events VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?)",
                             [eid, uid, event_name, value, run_id])
    except Exception as e:
        print(f"[App] Log Error: {e}")

def get_adopted_variant():
    """Check if there's an adopted experiment and return the winning variant."""
    global db_con
    import json

    try:
        if is_cloud_mode():
            # PostgreSQL mode
            pool = get_pg_pool()
            if pool:
                conn = pool.getconn()
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT variant_config
                            FROM adoptions
                            ORDER BY adopted_at DESC
                            LIMIT 1
                        """)
                        result = cur.fetchone()
                finally:
                    pool.putconn(conn)

                if result and result[0]:
                    variant_config = json.loads(result[0]) if isinstance(result[0], str) else result[0]
                    if variant_config and isinstance(variant_config, dict) and variant_config.get('winning_variant'):
                        logger.info(f"Adopted variant detected: {variant_config}")
                        return variant_config
        else:
            # DuckDB mode
            if not db_con:
                return None
            with db_lock:
                result = db_con.execute("""
                    SELECT variant_config
                    FROM adoptions
                    ORDER BY adopted_at DESC
                    LIMIT 1
                """).fetchone()

                if result and result[0]:
                    variant_config = json.loads(result[0])
                    if variant_config and isinstance(variant_config, dict) and variant_config.get('winning_variant'):
                        logger.info(f"Adopted variant detected: {variant_config}")
                        return variant_config
                    else:
                        logger.warning(f"Invalid variant_config found: {variant_config}")
    except Exception as e:
        logger.warning(f"No adoptions table or error: {e}")

    return None

def is_experiment_active():
    """Check if there's an active experiment running (supports both DuckDB and PostgreSQL)."""
    global db_con

    try:
        if is_cloud_mode():
            # PostgreSQL mode
            pool = get_pg_pool()
            if pool:
                conn = pool.getconn()
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1 FROM active_experiment WHERE is_active = true LIMIT 1")
                        result = cur.fetchone()
                        return result is not None
                finally:
                    pool.putconn(conn)
        else:
            # DuckDB mode
            if not db_con:
                return False
            with db_lock:
                result = db_con.execute("""
                    SELECT 1 FROM active_experiment WHERE is_active = true LIMIT 1
                """).fetchone()
                return result is not None
    except Exception as e:
        # Table doesn't exist yet = no active experiment
        return False

    return False

def get_assignment(uid: str):
    """
    Assignment logic for continuous experimentation:
    1. If experiment is active -> A/B split (A=current baseline, B=new variant)
    2. If no experiment but has adoption -> everyone sees adopted variant (baseline)
    3. If no experiment and no adoption -> default A/B split (initial state)
    """
    experiment_active = is_experiment_active()
    adopted = get_adopted_variant()

    if experiment_active:
        # Active experiment: A/B split
        # A = current baseline (adopted variant or original A)
        # B = new variant being tested
        hash_val = int(hashlib.md5(uid.encode()).hexdigest(), 16)
        variant = 'B' if (hash_val % 100) >= 50 else 'A'
        logger.info(f"Experiment active: {uid} -> {variant}")
        return variant

    if adopted:
        # No active experiment, but has adoption = show adopted variant to everyone
        winning = adopted.get('winning_variant', 'B')
        logger.info(f"No experiment, using adopted baseline: {winning}")
        return winning

    # Initial state: no experiment, no adoption = default A/B split
    hash_val = int(hashlib.md5(uid.encode()).hexdigest(), 16)
    return 'B' if (hash_val % 100) >= 50 else 'A'

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, uid: str = None, run_id: str = None, weight: float = 1.0):
    # 1. Check Query Param (Agent priority) -> 2. Cookie -> 3. New
    user_id = uid or request.cookies.get("user_id")
    is_new = False
    if not user_id:
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        is_new = True

    variant = get_assignment(user_id)
    adopted = get_adopted_variant()

    # Render
    response = templates.TemplateResponse("index.html", {
        "request": request,
        "uid": user_id,
        "variant": variant,
        "is_adopted": adopted is not None  # Flag to show adoption badge
    })

    if is_new or uid:  # Log assignment if new OR if explicitly passed (Agent run)
        try:
            if is_cloud_mode():
                # PostgreSQL mode
                pool = get_pg_pool()
                if pool:
                    conn = pool.getconn()
                    try:
                        with conn.cursor() as cur:
                            if run_id:
                                cur.execute("SELECT 1 FROM assignments WHERE user_id = %s AND run_id = %s", (user_id, run_id))
                            else:
                                cur.execute("SELECT 1 FROM assignments WHERE user_id = %s AND run_id IS NULL", (user_id,))
                            exists = cur.fetchone()

                            if not exists:
                                cur.execute(
                                    "INSERT INTO assignments (user_id, experiment_id, variant, assigned_at, run_id, weight) VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s, %s)",
                                    (user_id, 'exp_default', variant, run_id, weight)
                                )
                                print(f"[App] Logged assignment: {user_id} -> {variant} (run_id: {run_id}, weight: {weight})")
                        conn.commit()
                    finally:
                        pool.putconn(conn)
            else:
                # DuckDB mode
                global db_con
                if db_con:
                    with db_lock:
                        if run_id:
                            exists = db_con.execute("SELECT 1 FROM assignments WHERE user_id = ? AND run_id = ?", [user_id, run_id]).fetchone()
                        else:
                            exists = db_con.execute("SELECT 1 FROM assignments WHERE user_id = ? AND run_id IS NULL", [user_id]).fetchone()

                        if not exists:
                            db_con.execute("INSERT INTO assignments VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?)", [user_id, 'exp_default', variant, run_id, weight])
                            print(f"[App] Logged assignment: {user_id} -> {variant} (run_id: {run_id}, weight: {weight})")
        except Exception as e:
            print(f"[App] Assignment Log Error: {e}")

    if is_new:
        response.set_cookie(key="user_id", value=user_id)

    # Prevent browser caching to ensure variant changes are reflected immediately
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

@app.get("/cart", response_class=HTMLResponse)
async def view_cart(request: Request):
    uid = request.cookies.get("user_id") or "guest"
    group = get_assignment(uid)
    return templates.TemplateResponse("cart.html", {"request": request, "uid": uid, "group": group})

@app.get("/detail", response_class=HTMLResponse)
async def view_detail(request: Request, id: str = "item_001"):
    uid = request.cookies.get("user_id") or "guest"
    group = get_assignment(uid)
    return templates.TemplateResponse("detail.html", {"request": request, "uid": uid, "group": group, "item_id": id})

@app.get("/search", response_class=HTMLResponse)
async def view_search(request: Request, q: str = ""):
    uid = request.cookies.get("user_id") or "guest"
    group = get_assignment(uid)
    return templates.TemplateResponse("search.html", {"request": request, "uid": uid, "group": group, "query": q})

@app.get("/tracking", response_class=HTMLResponse)
async def view_tracking(request: Request):
    uid = request.cookies.get("user_id") or "guest"
    group = get_assignment(uid)
    return templates.TemplateResponse("tracking.html", {"request": request, "uid": uid, "group": group})

@app.post("/click")
async def track_click(uid: str = Form(...), element: str = Form(...), run_id: str = Form(None)):
    group = get_assignment(uid)
    log_event(uid, group, element, 0.0, run_id)
    return {"status": "success", "event": "click", "uid": uid}

@app.post("/order")
async def track_order(uid: str = Form(...), amount: float = Form(...), run_id: str = Form(None)):
    group = get_assignment(uid)
    log_event(uid, group, 'purchase', amount, run_id)
    return {"status": "success", "event": "order", "uid": uid}

from pydantic import BaseModel

class SqlRequest(BaseModel):
    sql: str

@app.post("/admin/execute_sql")
async def execute_sql(body: SqlRequest):
    global db_con
    if not db_con:
        return {"status": "error", "message": "DB not connected"}
    
    try:
        logger.info("Executing Admin SQL")
        with db_lock:
            result = None
            columns = []
            try:
                db_con.execute(body.sql)
                try:
                    result = db_con.fetchall()
                    if db_con.description:
                        columns = [desc[0] for desc in db_con.description]
                except Exception:
                    # Query probably didn't return rows (e.g. INSERT/UPDATE)
                    pass
                try:
                    db_con.execute("COMMIT")
                except Exception as e:
                    # DDLs like CREATE TABLE might auto-commit, causing "no transaction active" error
                    if "no transaction is active" in str(e).lower():
                        pass
                    else:
                        raise e
            except Exception as e:
                try:
                    db_con.execute("ROLLBACK")
                except Exception:
                    pass
                raise e
                
        return {"status": "success", "data": result, "columns": columns}

    except Exception as e:
        logger.error(f"SQL Exec Error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/admin/db_release")
async def release_db():
    """Release DB connection to allow external writes (for Streamlit)."""
    global db_con
    try:
        if db_con:
            db_con.close()
            db_con = None
            logger.info("DB connection released")
        return {"status": "success", "message": "DB connection released"}
    except Exception as e:
        logger.error(f"DB release error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/admin/db_reconnect")
async def reconnect_db():
    """Reconnect to DB after external writes."""
    global db_con
    try:
        if not db_con:
            db_con = duckdb.connect(DB_PATH)
            logger.info("DB reconnected in READ/WRITE mode")
        return {"status": "success", "message": "DB reconnected"}
    except Exception as e:
        logger.error(f"DB reconnect error: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Ensure tables exist before server start if running directly
    if not os.path.exists(DB_PATH):
        print(f"Creating DB at {DB_PATH}")
        try:
            con = duckdb.connect(DB_PATH)
            con.execute("CREATE TABLE IF NOT EXISTS events (event_id VARCHAR, user_id VARCHAR, event_name VARCHAR, timestamp TIMESTAMP, value DOUBLE, run_id VARCHAR)")
            con.execute("CREATE TABLE IF NOT EXISTS assignments (user_id VARCHAR, experiment_id VARCHAR, variant VARCHAR, assigned_at TIMESTAMP, run_id VARCHAR, weight FLOAT DEFAULT 1.0)")
            con.close()
        except:
            pass
            
    uvicorn.run(app, host="0.0.0.0", port=8000)
