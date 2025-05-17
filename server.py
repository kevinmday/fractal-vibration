# server.py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/nyt-webhook", methods=["POST"])
def nyt_webhook():
    data = request.json
    print("Received payload:", data)
    return jsonify({
        "status": "received",
        "headline": data.get("headline", "No headline provided")
    }), 200

if __name__ == "__main__":
    app.run(port=5000)
