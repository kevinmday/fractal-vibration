from flask import Flask, render_template, jsonify

app = Flask(__name__)

API_KEY = "PGS3HTS8QN46BJ5J"
BASE_URL = "https://www.alphavantage.co/query"

# Fetch stock data
def get_daily_stock_data(symbol):
    url = f"{BASE_URL}?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "Time Series (Daily)" not in data:
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
    ttcf = round((1 / (intention + 0.001)) * 1.5, 2)

    return {
        "price": round(latest_price, 2),
        "intention": round(intention, 4),
        "scale": round(scale, 4),
        "ttcf": ttcf
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
