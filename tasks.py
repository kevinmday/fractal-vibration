from celery import Celery

app = Celery("tasks", broker="memory://", backend="rpc://")
app.conf.task_always_eager = True  # Run tasks immediately

@app.task
def process_rss_entry(title, description):
    print(f"[MOCK RSS] Processing: {title}")
    sentiment = len(description) % 5  # Fake sentiment score
    print(f"[Sentiment Score]: {sentiment}")
    return sentiment

