from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import argparse
import sqlite3
import uvicorn
import os
import yfinance as yf

# ---------- APP SETUP ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.join(BASE_DIR, "static")
template_path = os.path.join(BASE_DIR, "templates")

app = FastAPI()
app.mount("/static", StaticFiles(directory=static_path), name="static")
templates = Jinja2Templates(directory=template_path)

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
        notes TEXT,
        level TEXT,
        source TEXT
    )
''')
conn.commit()

# ---------- DATA MODEL ----------
class IntentionUpdate(BaseModel):
    symbol: str
    direction: int = Field(..., ge=-1, le=1)
    scale: float = Field(..., ge=0.0, le=10.0)
    notes: str = ""

    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, v):
        return v.upper()

# ---------- REAL AUTO-SEEDING ----------
def auto_seed_from_yahoo():
    pyramid_targets = {
        "MARKET": ["SPY", "QQQ", "VIXY", "DXY"],
        "SECTOR": ["XLK", "XLE", "XLF", "XLV"],
        "ASSET": ["AAPL", "TSLA", "GOOG", "XOM", "JPM"]
    }

    now = datetime.utcnow().isoformat()

    for level, symbols in pyramid_targets.items():
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d", interval="1m")
                if hist.empty:
                    print(f"⚠️ No data for {symbol}")
                    continue
                last = hist.iloc[-1]
                close = last['Close']
                open_ = last['Open']
                direction = 1 if close > open_ else -1 if close < open_ else 0
                scale = round(abs((close - open_) / open_) * 10, 2)
                notes = f"Live auto-seed from Yahoo Finance: Open={open_}, Close={close}"

                c.execute("""
                    INSERT INTO asset_intention (symbol, timestamp, direction, scale, notes, level, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (symbol, now, direction, scale, notes, level, "live-autoseed"))

                print(f"✅ Seeded {symbol}: dir={direction}, scale={scale}")

            except Exception as e:
                print(f"❌ Failed to seed {symbol}: {e}")
    conn.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(auto_seed_from_yahoo, 'interval', minutes=10)
scheduler.start()

# ---------- ROUTES ----------
@app.get("/", response_class=HTMLResponse)
async def frontend(request: Request):
    return templates.TemplateResponse("seeder_dashboard_ver2.html", {"request": request})

@app.post("/update")
def update_intention(data: IntentionUpdate):
    now = datetime.utcnow().isoformat()
    c.execute("""
        INSERT INTO asset_intention (symbol, timestamp, direction, scale, notes, level, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (data.symbol, now, data.direction, data.scale, data.notes, "USER", "form"))
    conn.commit()
    return {"status": "success", "timestamp": now}

@app.get("/history/{symbol}")
def get_history(symbol: str):
    c.execute("""
        SELECT timestamp, direction, scale, notes, level, source
        FROM asset_intention
        WHERE symbol = ?
        ORDER BY timestamp DESC
    """, (symbol.upper(),))
    rows = c.fetchall()
    return {"symbol": symbol.upper(), "history": rows}

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
    symbol = symbol.upper()
    now = datetime.utcnow().isoformat()
    c.execute("""
        INSERT INTO asset_intention (symbol, timestamp, direction, scale, notes, level, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (symbol, now, direction, scale, notes, "USER", "form"))
    conn.commit()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": f"✅ Intention for {symbol} submitted!",
    })

# ---------- CLI ----------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MarketMind Seeder App")
    parser.add_argument("--run", action="store_true", help="Run the FastAPI server")
    args = parser.parse_args()

    if args.run or not args.run:
        uvicorn.run("marketmind_seeder_app_ver10:app", host="127.0.0.1", port=8000, reload=True)


