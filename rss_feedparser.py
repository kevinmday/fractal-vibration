import time
import feedparser
import requests

RSS_URL = "http://localhost:5001/mock_rss.xml"
WEBHOOK_URL = "http://localhost:5000/nyt-webhook"

# 🧠 Keep track of seen links (or titles if needed)
seen_links = set()

def check_feed():
    feed = feedparser.parse(RSS_URL)
    
    for entry in feed.entries:
        # ✅ Skip if we've already processed this item
        if entry.link in seen_links:
            continue
        
        seen_links.add(entry.link)  # 🧠 Remember this item

        # 📬 Send to your webhook (optional)
        payload = {
            "headline": entry.title,
            "summary": entry.description,
            "url": entry.link,
            "published_date": "",  # RSS doesn't always have this
            "byline": "RSS Agent"
        }
        response = requests.post(WEBHOOK_URL, json=payload)
        print(f"Sent: {entry.title} — Status: {response.status_code}")

if __name__ == "__main__":
    while True:
        print("Checking RSS feed...")
        check_feed()
        time.sleep(60)  # wait 60 seconds before polling again


