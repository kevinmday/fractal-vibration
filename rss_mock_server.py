from flask import Flask, Response

app = Flask(__name__)

@app.route("/mock_rss.xml")
def mock_rss():
    mock_data = """
    <rss version="2.0">
    <channel>
        <title>Mock Market Feed</title>
        <item>
            <title>AI Stocks Skyrocket</title>
            <description>Investors are bullish on AI-related tech.</description>
            <link>http://example.com/ai</link>
        </item>
        <item>
            <title>Recession Fears Grip Market</title>
            <description>Federal Reserve warns of inflationary pressures.</description>
            <link>http://example.com/recession</link>
        </item>
        <item>
            <title>Gold Prices Surge</title>
            <description>Investors turn to safe haven assets amid volatility.</description>
            <link>http://example.com/gold</link>
        </item>
    </channel>
    </rss>
    """
    return Response(mock_data, mimetype='application/rss+xml')

if __name__ == "__main__":
    app.run(port=5001)
