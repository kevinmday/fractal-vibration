from flask import Flask, render_template, jsonify, request
import requests
import datetime

app = Flask(__name__)

# --- Alpha Vantage Configuration ---
API_KEY = "PGS3HTS8QN46BJ5J"
BASE_URL = "https://www.alphavantage.co/query"
USE_MOCK_DATA = True  # Toggle for mock or live API

# --- PredictiveScaleAgent Definition ---
class PredictiveScaleAgent:
    def __init__(self, api_key, webhook_urls, scale_threshold=0.05, prediction_threshold=0.01):
        self.api_key = api_key
        self.api_url = 'https://www.alphavantage.co/query'
        self.scale_cache = {}
        self.latest_scale = {}
        self.webhook_urls = webhook_urls
        self.scale_threshold = scale_threshold
        self.prediction_threshold = prediction_threshold

    def fetch_scale(self, ticker):
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': ticker,
            'apikey': self.api_key
        }
        try:
            response = requests.get(self.api_url, params=params)
            data = response.json()
            volume = int(data['Global Quote']['06. volume'])
            latest_price = float(data['Global Quote']['05. price'])

            scale = round(volume / 1_000_000, 2)

            if ticker not in self.scale_cache:
                self.scale_cache[ticker] = []
            self.scale_cache[ticker].append(scale)
            if len(self.scale_cache[ticker]) > 5:
                self.scale_cache[ticker] = self.scale_cache[ticker][-5:]

            previous_scale = self.latest_scale.get(ticker, scale)
            scale_change = (scale - previous_scale) / previous_scale if previous_scale else 0

            if abs(scale_change) >= self.scale_threshold:
                shift_type = "scaling up" if scale_change > 0 else "scaling down"
                payload = {
                    "event": "immediate_scale_shift",
                    "ticker": ticker,
                    "scale": scale,
                    "intention": round(abs(scale_change) * 100, 2),
                    "volume": volume,
                    "shift_type": shift_type,
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
                }
                self.send_webhook(payload)

            prediction = self.predict_scale_shift(ticker)
            if prediction:
                pred_payload = {
                    "event": "early_prediction",
                    "ticker": ticker,
                    "prediction": prediction,
                    "recent_scales": self.scale_cache[ticker],
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
                }
                self.send_webhook(pred_payload)

            self.latest_scale[ticker] = scale
            return scale

        except (KeyError, ValueError, requests.RequestException) as e:
            print(f"[PredictiveScaleAgent Error]: {e}")
            return self.latest_scale.get(ticker, 1.0)

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
        else:
            return None

    def send_webhook(self, payload):
        headers = {'Content-Type': 'application/json'}
        for url in self.webhook_urls:
            try:
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    print(f"[Webhook]: Successfully sent to {url}")
                else:
                    print(f"[Webhook]: Failed to send to {url} (Status: {response.status_code})")
            except requests.RequestException as e:
                print(f"[Webhook Error]: {e}")

# --- Mock Data for IBM ---
MOCK_IBM_DATA = {
    "Time Series (Daily)": {
        "2025-04-25": {"1. open": "140.00", "2. high": "142.00", "3. low": "138.50", "4. close": "141.75", "5. volume": "5012000"},
        "2025-04-24": {"1. open": "138.50", "2. high": "141.00", "3. low": "137.00", "4. close": "139.25", "5. volume": "4789000"},
        "2025-04-23": {"1. open": "139.00", "2. high": "140.50", "3. low": "136.50", "4. close": "137.75", "5. volume": "5123000"},
        "2025-04-22": {"1. open": "137.00", "2. high": "139.50", "3. low": "135.25", "4. close": "138.00", "5. volume": "4600000"},
        "2025-04-21": {"1. open": "134.75", "2. high": "137.00", "3. low": "133.50", "4. close": "136.25", "5. volume": "4905000"},
        "2025-04-18": {"1. open": "133.00", "2. high": "135.00", "3. low": "132.25", "4. close": "134.50", "5. volume": "4700000"},
        "2025-04-17": {"1. open": "130.50", "2. high": "133.75", "3. low": "129.75", "4. close": "132.25", "5. volume": "5108000"},
        "2025-04-16": {"1. open": "128.00", "2. high": "131.00", "3. low": "127.50", "4. close": "130.00", "5. volume": "4987000"},
        "2025-04-15": {"1. open": "127.00", "2. high": "129.00", "3. low": "126.00", "4. close": "128.25", "5. volume": "5234000"},
        "2025-04-14": {"1. open": "126.25", "2. high": "128.00", "3. low": "125.50", "4. close": "127.50", "5. volume": "4700000"}
    }
}

# --- Predictive Agent Initialization ---
AGENT = PredictiveScaleAgent(
    api_key="4F9GRQRMNIAK1CLV",
    webhook_urls=[],
    scale_threshold=0.05,
    prediction_threshold=0.01
)

# --- Stock Data & Metric Calculation ---
def get_daily_stock_data(symbol):
    if USE_MOCK_DATA and symbol.upper() == "IBM":
        print(f"[MOCK] Returning mock data for IBM")
        return MOCK_IBM_DATA["Time Series (Daily)"]

    url = f"{BASE_URL}?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "Time Series (Daily)" not in data:
        print("[ERROR] Unexpected API response")
        return None

    return data["Time Series (Daily)"]

def calculate_metrics(data):
    closes = [float(data[date]['4. close']) for date in sorted(data.keys(), reverse=True)[:6]]
    if len(closes) < 6:
        return None

    latest_price = closes[0]
    prev_price = closes[1]
    oldest_price = closes[-1]

    raw_intention = (latest_price - oldest_price) / oldest_price
    intention_score = round(abs(raw_intention) * 100, 2)

    raw_scale = (latest_price - prev_price) / prev_price
    scale_score = round(abs(raw_scale) * 100, 2)

    raw_ttcf = (1 / (abs(raw_intention) + 0.001)) * 1.5
    ttcf_score = min(100, round(raw_ttcf, 2))

    return {
        "price": round(latest_price, 2),
        "intention": intention_score,
        "scale": scale_score,
        "ttcf": ttcf_score
    }

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stock/<symbol>')
def stock_data(symbol):
    data = get_daily_stock_data(symbol)
    if not data:
        return jsonify({"error": "Failed to retrieve data"}), 400

    metrics = calculate_metrics(data)
    if not metrics:
        return jsonify({"error": "Insufficient data"}), 400

    live_scale = AGENT.fetch_scale(symbol.upper())

    return jsonify({
        "symbol": symbol.upper(),
        "price": metrics["price"],
        "ucip_force": metrics["intention"],
        "fils": live_scale,
        "ttcf": metrics["ttcf"]
    })

# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)
