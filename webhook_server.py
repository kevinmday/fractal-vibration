from flask import Flask, request, jsonify
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging
import csv
from datetime import datetime

# Initialize Flask app and logger
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Function to log sentiment analysis to CSV
def log_to_csv(data, label, score):
    with open("webhook_logs.csv", mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now(), data.get("summary", ""), label, score])

# Define the webhook route
@app.route("/nyt-webhook", methods=["POST"])
def nyt_webhook():
    data = request.get_json(force=True)
    logging.info("Webhook received: %s", data)

    # Use summary or fallback to headline
    text_to_analyze = data.get("summary") or data.get("headline") or ""

    if not text_to_analyze:
        return jsonify({"status": "error", "message": "No text to analyze"}), 400

    scores = analyzer.polarity_scores(text_to_analyze)
    compound = scores["compound"]

    if compound >= 0.05:
        label = "POSITIVE"
    elif compound <= -0.05:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"

    confidence = round(abs(compound), 4)

    # Log to CSV
    log_to_csv(data, label, confidence)

    # Return response
    return jsonify({
        "status": "received",
        "label": label,
        "confidence": confidence
    }), 200

# Run the server
if __name__ == "__main__":
    app.run(port=5000, debug=True)

