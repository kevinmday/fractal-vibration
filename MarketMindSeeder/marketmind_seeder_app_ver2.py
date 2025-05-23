from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
import argparse
import random
import sqlite3

import uvicorn

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")



# ---------- DATABASE SETUP ----------
conn = sqlite3.connect("marketmind_seeder.db", check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS asset_intention (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        timestamp TEXT,
        direction INTEGER,
        scale REAL,
        notes TEXT
    )
''')
conn.commit()

# ---------- DATA MODEL ----------
class IntentionUpdate(BaseModel):
    symbol: str
    direction: int  # -1, 0, +1
    scale: float    # 0.0 to 10.0
    notes: str = ""

# ---------- ROUTES ----------
@app.get("/", response_class=HTMLResponse)
async def frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/update")
def update_intention(data: IntentionUpdate):
    now = datetime.utcnow().isoformat()
    c.execute("""
        INSERT INTO asset_intention (symbol, timestamp, direction, scale, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (data.symbol, now, data.direction, data.scale, data.notes))
    conn.commit()
    return {"status": "success", "timestamp": now}

@app.get("/history/{symbol}")
def get_history(symbol: str):
    c.execute("SELECT timestamp, direction, scale, notes FROM asset_intention WHERE symbol = ? ORDER BY timestamp DESC", (symbol,))
    rows = c.fetchall()
    return {"symbol": symbol, "history": rows}

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

# Setup templates
templates = Jinja2Templates(directory="templates")

@app.get("/form", response_class=HTMLResponse)
def show_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/form/submit", response_class=HTMLResponse)
def submit_form(
    request: Request,
    symbol: str = Form(...),
    direction: int = Form(...),
    scale: float = Form(...),
    notes: str = Form("")
):
    now = datetime.utcnow().isoformat()
    c.execute("""
        INSERT INTO asset_intention (symbol, timestamp, direction, scale, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (symbol.upper(), now, direction, scale, notes))
    conn.commit()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": f"✅ Intention for {symbol.upper()} submitted!",
    })


# ---------- MOCK SEEDER ----------
def mock_update():
    symbols = ["AAPL", "MSFT", "GOOG", "TSLA", "BTC-USD"]
    for symbol in symbols:
        direction = random.choice([-1, 0, 1])
        scale = round(random.uniform(0.0, 10.0), 2)
        notes = "Mock update for seeding"
        now = datetime.utcnow().isoformat()
        c.execute("""
            INSERT INTO asset_intention (symbol, timestamp, direction, scale, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (symbol, now, direction, scale, notes))
    conn.commit()
    print("✅ Mock data seeded for assets:", symbols)

# ---------- CLI ----------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MarketMind Seeder App")
    parser.add_argument("--seed", action="store_true", help="Seed mock data into the database")
    parser.add_argument("--run", action="store_true", help="Run the FastAPI server")
    args = parser.parse_args()

    if args.seed:
        mock_update()

    if args.run:
        uvicorn.run("marketmind_seeder_app:app", host="127.0.0.1", port=8000, reload=True)
