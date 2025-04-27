from flask import Flask, render_template, request
from googleapiclient.discovery import build
import os
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = os.environ.get("YOUTUBE_API_KEY")

@app.route('/healthz')
def health_check():
    return "ok", 200

@app.route('/')
def home():
    return "Service Running", 200

@app.route('/search')
def search():
    keyword = request.args.get("keyword", "")
    youtube = build("youtube", "v3", developerKey=API_KEY)

    search_response = youtube.search().list(
        q=keyword,
        type="channel",
        part="snippet",
        maxResults=20,
        order="date",
        publishedAfter=(datetime.utcnow() - timedelta(days=180)).isoformat("T") + "Z"
    ).execute()

    channels = []
    seen_channel_ids = set()
    for item in search_response.get("items", []):
        channel_id = item["snippet"]["channelId"]
        if channel_id in seen_channel_ids:
            continue
        seen_channel_ids.add(channel_id)

        channel_title = item["snippet"]["channelTitle"]
        published_at = item["snippet"]["publishedAt"]

        ch_info = youtube.channels().list(
            part="statistics",
            id=channel_id
        ).execute()

        if ch_info["items"]:
            stats = ch_info["items"][0]["statistics"]
            subs = int(stats.get("subscriberCount", 0))
            views = int(stats.get("viewCount", 0))
            months = max((datetime.utcnow() - datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")).days / 30, 1)
            income = int((views / months) * 0.3)

            channels.append({
                "title": channel_title,
                "subs": f"{subs:,}",
                "views": f"{views:,}",
                "income": f"{income:,} 円/月",
                "published_at": published_at[:10]
            })

    return render_template('index.html', channels=channels, keyword=keyword)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
