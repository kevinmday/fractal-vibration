import requests
import json
from flask import Flask, render_template, jsonify, request

webhook_url = "http://127.0.0.1:5000/nyt-webhook"



fake_payload = {
    "headline": "New Discovery in Ancient City",
    "byline": "By Jane Doe",
    "published_date": "2025-04-30T14:00:00Z",
    "summary": "Archaeologists uncovered a hidden temple under the ruins of Babylon.",
    "url": "https://www.nytimes.com/2025/04/30/science/babylon-temple-discovery.html"
}

response = requests.post(webhook_url, json=fake_payload)
print("Response:", response.json())
