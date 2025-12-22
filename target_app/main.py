from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import duckdb
import os
from datetime import datetime
import random

app = FastAPI()

# Fix Template Directory Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# DB Connection
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), 'novarium_local.db')

def log_event(uid, eid, event_name):
    try:
        con = duckdb.connect(DB_PATH)
        con.execute(f"INSERT INTO events VALUES ('{eid}', '{uid}', '{event_name}', CURRENT_TIMESTAMP)")
        con.close()
    except Exception as e:
        print(f"Log Error: {e}")

def get_assignment(uid):
    # Simple Hash Assignment (Deterministic)
    import hashlib
    hash_obj = hashlib.md5(str(uid).encode())
    val = int(hash_obj.hexdigest(), 16) % 100
    # 50/50 Split
    variant = 'B' if val >= 50 else 'A'
    return variant

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, uid: str = "guest"):
    variant = get_assignment(uid)
    
    # Log Assignment
    try:
        con = duckdb.connect(DB_PATH)
        con.execute(f"INSERT INTO assignments VALUES ('{uid}', 'exp_main', '{variant}', CURRENT_TIMESTAMP)")
        con.close()
    except Exception as e:
        # Expected if table locked or other issue, just print for debug
        print(f"Assignment Log Error: {e}")

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "uid": uid,
        "variant": variant
    })

@app.post("/click")
async def track_click(uid: str = Form(...), element: str = Form(...)):
    log_event(uid, 'exp_main', element)
    return {"status": "success", "event": "click", "uid": uid}

@app.post("/order")
async def track_order(uid: str = Form(...), amount: int = Form(...)):
    log_event(uid, 'exp_main', 'purchase')
    return {"status": "success", "event": "order", "uid": uid}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
