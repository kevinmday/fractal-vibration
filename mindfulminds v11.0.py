from flask import Flask, render_template, jsonify, request
import requests
from datetime import datetime
import threading
import time

app = Flask(__name__)

# --- Configuration ---
API_KEY = "PGS3HTS8QN46BJ5J"
BASE_URL = "https://www.alphavantage.co/query"
USE_MOCK_DATA = True

# --- Mock IBM Data ---
MOCK_IBM_DATA = {
    "Time Series (Daily)": {
        "2025-04-25": {"4. close": "141.75", "5. volume": "5012000"},
        "2025-04-24": {"4. close": "139.25", "5. volume": "4789000"},
        "2025-04-23": {"4. close": "137.75", "5. volume": "5123000"},
        "2025-04-22": {"4. close": "138.00", "5. volume": "4600000"},
        "2025-04-21": {"4. close": "136.25", "5. volume": "4905000"},
        "2025-04-18": {"4. close": "134.50", "5. volume": "4700000"}
    }
}

# --- PredictiveScaleAgent ---
class PredictiveScaleAgent:
    def __init__(self, api_key, webhook_urls=None, scale_threshold=0.05, prediction_threshold=0.01):
        self.api_key = api_key
        self.api_url = BASE_URL
        self.scale_cache = {}
        self.latest_scale = {}
        self.webhook_urls = webhook_urls or []
        self.scale_threshold = scale_threshold
        self.prediction_threshold = prediction_threshold

    def fetch_scale(self, ticker):
        if USE_MOCK_DATA and ticker.upper() == "IBM":
            volume = int(MOCK_IBM_DATA["Time Series (Daily)"]["2025-04-25"]["5. volume"])
            price = float(MOCK_IBM_DATA["Time Series (Daily)"]["2025-04-25"]["4. close"])
        else:
            try:
                params = {'function': 'GLOBAL_QUOTE', 'symbol': ticker, 'apikey': self.api_key}
                response = requests.get(self.api_url, params=params)
                data = response.json()
                volume = int(data['Global Quote']['06. volume'])
                price = float(data['Global Quote']['05. price'])
            except Exception as e:
                print(f"[Error]: Fetching live scale failed for {ticker}: {e}")
                return self.latest_scale.get(ticker, 1.0)

        scale = round(volume / 1_000_000, 2)
        history = self.scale_cache.setdefault(ticker, [])
        history.append(scale)
        if len(history) > 5:
            self.scale_cache[ticker] = history[-5:]

        prev = self.latest_scale.get(ticker, scale)
        change = (scale - prev) / prev if prev else 0

        if abs(change) >= self.scale_threshold:
            self.send_webhook({
                "event": "immediate_scale_shift",
                "ticker": ticker,
                "scale": scale,
                "intention": round(abs(change) * 100, 2),
                "volume": volume,
                "shift_type": "scaling up" if change > 0 else "scaling down",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

        prediction = self.predict_scale_shift(ticker)
        if prediction:
            self.send_webhook({
                "event": "early_prediction",
                "ticker": ticker,
                "prediction": prediction,
                "recent_scales": self.scale_cache[ticker],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

        self.latest_scale[ticker] = scale
        return scale

    def predict_scale_shift(self, ticker):
        history = self.scale_cache.get(ticker, [])
        if len(history) < 3:
            return None
        rates = [(history[i+1] - history[i]) / history[i] for i in range(len(history)-1)]
        avg_rate = sum(rates) / len(rates)
        if avg_rate > self.prediction_threshold:
            return "potential_upscale"
        elif avg_rate < -self.prediction_threshold:
            return "potential_downscale"
        return None

    def send_webhook(self, payload):
        headers = {'Content-Type': 'application/json'}
        for url in self.webhook_urls:
            try:
                res = requests.post(url, json=payload, headers=headers)
                if res.status_code == 200:
                    print(f"[Webhook]: Sent successfully to {url}")
                else:
                    print(f"[Webhook]: Failed (status: {res.status_code})")
            except requests.RequestException as e:
                print(f"[Webhook Error]: {e}")

# --- Stock Data Fetching ---
def get_daily_stock_data(symbol):
    if USE_MOCK_DATA and symbol.upper() == "IBM":
        return MOCK_IBM_DATA["Time Series (Daily)"]

    try:
        params = {'function': 'TIME_SERIES_DAILY', 'symbol': symbol, 'apikey': API_KEY}
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        return data.get("Time Series (Daily)")
    except Exception as e:
        print(f"[Data Error]: {e}")
        return None

# --- Metrics Calculation ---
def calculate_metrics(data, f_int_sent=None):
    closes = [float(data[date]['4. close']) for date in sorted(data.keys(), reverse=True)[:6]]
    if len(closes) < 6:
        return None

    latest, prev, oldest = closes[0], closes[1], closes[-1]
    raw_int = (latest - oldest) / oldest
    raw_scale = (latest - prev) / prev
    raw_ttcf = (1 / (abs(raw_int) + 0.001)) * 1.5

    int_score = round(abs(raw_int) * 100, 2)
    scale_score = round(abs(raw_scale) * 100, 2)
    ttcf_score = min(100, round(raw_ttcf, 2))

    if f_int_sent is not None:
        int_score = round(int_score * (1 + (f_int_sent / 100)), 2)

    return {
        "price": round(latest, 2),
        "intention": int_score,
        "scale": scale_score,
        "ttcf": ttcf_score,
        "f_int_sent": round(f_int_sent, 3) if f_int_sent is not None else None
    }

# --- Predictive Agent Initialization ---
AGENT = PredictiveScaleAgent(
    api_key=API_KEY,
    webhook_urls=[],
    scale_threshold=0.05,
    prediction_threshold=0.01
)

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stock/<symbol>')
def stock(symbol):
    symbol = symbol.upper()
    data = get_daily_stock_data(symbol)
    if not data:
        return jsonify({"error": "Data unavailable"}), 400

    metrics = calculate_metrics(data)
    if not metrics:
        return jsonify({"error": "Not enough data"}), 400

    scale = AGENT.fetch_scale(symbol)
    return jsonify({
        "symbol": symbol,
        "price": metrics["price"],
        "ucip_force": metrics["intention"],
        "fils": scale,
        "ttcf": metrics["ttcf"]
    })

# --- Run Server ---
if __name__ == '__main__':
    app.run(debug=True)
