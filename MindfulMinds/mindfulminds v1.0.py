from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

import requests
import json

import requests

API_KEY = "PGS3HTS8QN46BJ5J"
BASE_URL = "https://www.alphavantage.co/query"
USE_MOCK_DATA = True  # Toggle for mock or live API

# Mock data for IBM – 10 days
MOCK_IBM_DATA = {
    "Time Series (Daily)": {
        "2025-04-25": {
            "1. open": "140.00",
            "2. high": "142.00",
            "3. low": "138.50",
            "4. close": "141.75",
            "5. volume": "5012000"
        },
        "2025-04-24": {
            "1. open": "138.50",
            "2. high": "141.00",
            "3. low": "137.00",
            "4. close": "139.25",
            "5. volume": "4789000"
        },
        "2025-04-23": {
            "1. open": "139.00",
            "2. high": "140.50",
            "3. low": "136.50",
            "4. close": "137.75",
            "5. volume": "5123000"
        },
        "2025-04-22": {
            "1. open": "137.00",
            "2. high": "139.50",
            "3. low": "135.25",
            "4. close": "138.00",
            "5. volume": "4600000"
        },
        "2025-04-21": {
            "1. open": "134.75",
            "2. high": "137.00",
            "3. low": "133.50",
            "4. close": "136.25",
            "5. volume": "4905000"
        },
        "2025-04-18": {
            "1. open": "133.00",
            "2. high": "135.00",
            "3. low": "132.25",
            "4. close": "134.50",
            "5. volume": "4700000"
        },
        "2025-04-17": {
            "1. open": "130.50",
            "2. high": "133.75",
            "3. low": "129.75",
            "4. close": "132.25",
            "5. volume": "5108000"
        },
        "2025-04-16": {
            "1. open": "128.00",
            "2. high": "131.00",
            "3. low": "127.50",
            "4. close": "130.00",
            "5. volume": "4987000"
        },
        "2025-04-15": {
            "1. open": "127.00",
            "2. high": "129.00",
            "3. low": "126.00",
            "4. close": "128.25",
            "5. volume": "5234000"
        },
        "2025-04-14": {
            "1. open": "126.25",
            "2. high": "128.00",
            "3. low": "125.50",
            "4. close": "127.50",
            "5. volume": "4700000"
        }
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

    # Real API call (if USE_MOCK_DATA is False)
    url = f"{BASE_URL}?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "Time Series (Daily)" not in data:
        print("[ERROR] Unexpected API response")
        return None

    return data["Time Series (Daily)"]



# Calculate metrics
def calculate_metrics(data):
    closes = [float(data[date]['4. close']) for date in sorted(data.keys(), reverse=True)[:6]]

    if len(closes) < 6:
        return None

    latest_price = closes[0]
    scale = abs(latest_price - closes[1]) / closes[1]
    intention = abs(latest_price - closes[-1]) / closes[-1]
    
    # TTCF normalized to 0–100
    raw_ttcf = (1 / (intention + 0.001)) * 1.5
    ttcf = min(100, round(raw_ttcf, 2))  # cap at 100 if needed

    return {
        "price": round(latest_price, 2),
        "intention": round(intention * 100, 2),  # now 0–100
        "scale": round(scale * 100, 2),          # now 0–100
        "ttcf": ttcf                             # now normalized 0–100
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
