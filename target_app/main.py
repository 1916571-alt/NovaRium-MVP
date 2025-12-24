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

def log_event(uid, group, event_name, value=0.0):
    try:
        con = get_db_connection()
        # Ensure tables exist (Just in case, though they should exist from setup)
        con.execute("CREATE TABLE IF NOT EXISTS events (event_id VARCHAR, user_id VARCHAR, event_name VARCHAR, timestamp TIMESTAMP, value DOUBLE)")
        con.execute("CREATE TABLE IF NOT EXISTS assignments (user_id VARCHAR, group_id VARCHAR, assigned_at TIMESTAMP)")
        
        # Log
        eid = str(uuid.uuid4())
        # Use simple f-string query for MVP performance/simplicity or parameterized if wrapper allows
        con.execute(f"INSERT INTO events VALUES ('{eid}', '{uid}', '{event_name}', CURRENT_TIMESTAMP, {value})")
        con.close()
    except Exception as e:
        print(f"Log Error: {e}")
        try:
            con.close()
        except:
            pass

def get_assignment(uid: str):
    # Deterministic Split
    hash_val = int(hashlib.sha256(uid.encode()).hexdigest(), 16)
    return 'B' if (hash_val % 100) >= 50 else 'A' # 50:50 Split

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Simple Cookie-based ID
    uid = request.cookies.get("user_id")
    is_new = False
    if not uid:
        uid = f"user_{uuid.uuid4().hex[:8]}"
        is_new = True
    
    group = get_assignment(uid)
    
    # Render
    response = templates.TemplateResponse("index.html", {
        "request": request,
        "uid": uid,
        "group": group
    })
    
    if is_new:
        response.set_cookie(key="user_id", value=uid)
        
        # Log Assignment if new
        try:
            con = get_db_connection()
            # Check if exists (Double check)
            exists = con.execute(f"SELECT 1 FROM assignments WHERE user_id = '{uid}'").fetchone()
            if not exists:
                con.execute(f"INSERT INTO assignments VALUES ('{uid}', '{group}', CURRENT_TIMESTAMP)")
            con.close()
        except Exception as e:
            print(f"Assignment Log Error: {e}")
            try:
                con.close()
            except:
                pass
        
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
