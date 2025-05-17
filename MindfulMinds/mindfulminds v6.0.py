from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

API_KEY = "PGS3HTS8QN46BJ5J"
BASE_URL = "https://www.alphavantage.co/query"
USE_MOCK_DATA = True  # Toggle for mock or live API

# Mock data for IBM – 10 days
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

def get_daily_stock_data(symbol):
    if USE_MOCK_DATA:
        if symbol.upper() == "IBM":
            print(f"[MOCK] Returning mock data for IBM")
            return MOCK_IBM_DATA["Time Series (Daily)"]
        else:
            print(f"[MOCK] No mock data available for {symbol}")
            return None

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

    return jsonify({
        "symbol": symbol.upper(),
        "price": metrics["price"],
        "ucip_force": metrics["intention"],
        "fils": metrics["scale"],
        "ttcf": metrics["ttcf"]
    })

if __name__ == '__main__':
    app.run(debug=True)

