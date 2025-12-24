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

app = FastAPI()

# Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Mount Static
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), 'novarium_local.db')

# Ensure DB Connected
def get_db_connection():
    return duckdb.connect(DB_PATH)

def log_event(uid, variant, event_name, value=0.0):
    try:
        con = get_db_connection()
        # Ensure tables exist
        con.execute("CREATE TABLE IF NOT EXISTS events (event_id VARCHAR, user_id VARCHAR, event_name VARCHAR, timestamp TIMESTAMP, value DOUBLE)")
        con.execute("CREATE TABLE IF NOT EXISTS assignments (user_id VARCHAR, variant VARCHAR, assigned_at TIMESTAMP)")
        
        # Log
        eid = str(uuid.uuid4())
        con.execute(f"INSERT INTO events VALUES ('{eid}', '{uid}', '{event_name}', CURRENT_TIMESTAMP, {value})")
        con.close()
    except Exception as e:
        print(f"Log Error: {e}")
        try:
            con.close()
        except:
            pass

def get_assignment(uid: str):
    # Deterministic Split - Standardized to MD5 to match stats.py
    hash_val = int(hashlib.md5(uid.encode()).hexdigest(), 16)
    return 'B' if (hash_val % 100) >= 50 else 'A' # 50:50 Split

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, uid: str = None):
    # 1. Check Query Param (Agent priority) -> 2. Cookie -> 3. New
    user_id = uid or request.cookies.get("user_id")
    is_new = False
    if not user_id:
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        is_new = True
    
    variant = get_assignment(user_id)
    
    # Render
    response = templates.TemplateResponse("index.html", {
        "request": request,
        "uid": user_id,
        "variant": variant
    })
    
    if is_new or uid:  # Log assignment if new OR if explicitly passed (Agent run)
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                con = get_db_connection()
                # Ensure table exists
                con.execute("CREATE TABLE IF NOT EXISTS assignments (user_id VARCHAR, variant VARCHAR, assigned_at TIMESTAMP)")
                # Check if exists using prepared statement
                exists = con.execute("SELECT 1 FROM assignments WHERE user_id = ?", [user_id]).fetchone()
                if not exists:
                    con.execute("INSERT INTO assignments VALUES (?, ?, CURRENT_TIMESTAMP)", [user_id, variant])
                    print(f"[INFO] Logged assignment: {user_id} → {variant}")
                else:
                    print(f"[DEBUG] Assignment already exists for {user_id}")
                con.close()
                break  # Success, exit retry loop
            except Exception as e:
                error_msg = str(e).lower()
                # Check if it's a lock error
                if ('lock' in error_msg or 'cannot open' in error_msg or 'access' in error_msg) and attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"[WARN] DB locked for {user_id}, retrying in {wait_time:.2f}s... (Attempt {attempt + 1}/{max_retries})")
                    import time
                    time.sleep(wait_time)
                    try:
                        con.close()
                    except:
                        pass
                    continue
                else:
                    # Non-lock error or final retry failed
                    print(f"[ERROR] Assignment Log Error for {user_id}: {e}")
                    import traceback
                    traceback.print_exc()
                    try:
                        con.close()
                    except:
                        pass
                    break
            
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
async def track_click(uid: str = Form(...), element: str = Form(...)):
    group = get_assignment(uid)
    log_event(uid, group, element, 0.0)
    return {"status": "success", "event": "click", "uid": uid}

@app.post("/order")
async def track_order(uid: str = Form(...), amount: float = Form(...)):
    group = get_assignment(uid)
    log_event(uid, group, 'purchase', amount)
    return {"status": "success", "event": "order", "uid": uid}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
