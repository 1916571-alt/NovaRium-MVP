from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import duckdb
import os
from datetime import datetime
import hashlib
import uuid
import threading
import logging

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TargetApp")

app = FastAPI()

# Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Mount Static
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), 'novarium_local.db')

# Singleton DB Connection
db_con = None
db_lock = threading.Lock()

@app.on_event("startup")
async def startup_event():
    global db_con
    try:
        logger.info(f"Connecting to DB at {DB_PATH}")
        # Use READ ONLY mode to avoid locking issues with Streamlit
        db_con = duckdb.connect(DB_PATH, read_only=True)

        logger.info("DB Connected in READ ONLY mode")
    except Exception as e:
        logger.error(f"DB Startup Error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    global db_con
    if db_con:
        db_con.close()
        logger.info("DB Connection Closed")

def log_event(uid, variant, event_name, value=0.0, run_id=None):
    try:
        eid = str(uuid.uuid4())
        # Use simple print for user feedback as requested
        print(f"[App] Logging Event: {event_name} by {uid} (Value: {value})")

        # Use temporary connection for writing to avoid locking with Streamlit
        with duckdb.connect(DB_PATH) as write_con:
            write_con.execute("INSERT INTO events VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?)",
                         [eid, uid, event_name, value, run_id])
    except Exception as e:
        print(f"[App] Log Error: {e}")

def get_adopted_variant():
    """Check if there's an adopted experiment and return the winning variant."""
    global db_con
    if not db_con:
        return None

    try:
        with db_lock:
            # Get the most recent adoption
            result = db_con.execute("""
                SELECT variant_config
                FROM adoptions
                ORDER BY adopted_at DESC
                LIMIT 1
            """).fetchone()

            if result:
                import json
                variant_config = json.loads(result[0])
                logger.info(f"Adopted variant detected: {variant_config}")
                return variant_config
    except Exception as e:
        logger.warning(f"No adoptions table or error: {e}")

    return None

def get_assignment(uid: str):
    # Check if there's an adopted variant first
    adopted = get_adopted_variant()
    if adopted:
        # If experiment was adopted, show winning variant to everyone
        logger.info("Using adopted variant for all users")
        return 'B'  # Adopted variant is always the test variant

    # Otherwise, use deterministic split for A/B testing
    hash_val = int(hashlib.md5(uid.encode()).hexdigest(), 16)
    return 'B' if (hash_val % 100) >= 50 else 'A' # 50:50 Split

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
            # Use temporary connection for writing
            with duckdb.connect(DB_PATH) as write_con:
                # Check if exists for this run (if run_id provided)
                if run_id:
                    exists = write_con.execute("SELECT 1 FROM assignments WHERE user_id = ? AND run_id = ?", [user_id, run_id]).fetchone()
                else:
                    exists = write_con.execute("SELECT 1 FROM assignments WHERE user_id = ? AND run_id IS NULL", [user_id]).fetchone()

                if not exists:
                    write_con.execute("INSERT INTO assignments VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?)", [user_id, 'exp_default', variant, run_id, weight])
                    print(f"[App] Logged assignment: {user_id} -> {variant} (run_id: {run_id}, weight: {weight})")
        except Exception as e:
            print(f"[App] Assignment Log Error: {e}")

    if is_new:
        response.set_cookie(key="user_id", value=user_id)

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
    try:
        logger.info("Executing Admin SQL")

        # Determine if this is a write operation (CREATE, INSERT, UPDATE, DELETE, etc.)
        sql_upper = body.sql.strip().upper()
        is_write_op = any(sql_upper.startswith(kw) for kw in ['CREATE', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER'])

        result = None
        columns = []

        if is_write_op:
            # Use temporary write connection for write operations
            logger.info("Using write connection for admin SQL")
            with duckdb.connect(DB_PATH) as write_con:
                try:
                    write_con.execute(body.sql)
                    try:
                        result = write_con.fetchall()
                        if write_con.description:
                            columns = [desc[0] for desc in write_con.description]
                    except Exception:
                        # Query probably didn't return rows (e.g. INSERT/UPDATE)
                        pass
                except Exception as e:
                    raise e
        else:
            # Use read-only connection for SELECT queries
            logger.info("Using read-only connection for admin SQL")
            with db_lock:
                try:
                    result = db_con.execute(body.sql).fetchall()
                    if db_con.description:
                        columns = [desc[0] for desc in db_con.description]
                except Exception as e:
                    raise e

        return {"status": "success", "data": result, "columns": columns}

    except Exception as e:
        logger.error(f"SQL Exec Error: {e}")
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
