from tasks import process_rss_entry

MOCK_FEED = [
    {"title": "AI Stocks Surge", "description": "Bullish investors drive tech rally."},
    {"title": "Fed Hikes Rates", "description": "Recession fears increase."},
]

def simulate_rss_ingestion():
    for entry in MOCK_FEED:
        process_rss_entry.delay(entry["title"], entry["description"])

if __name__ == "__main__":
    simulate_rss_ingestion()
