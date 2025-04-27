
import os
from flask import Flask, request, render_template
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import math

app = Flask(__name__)

API_KEY = os.environ.get("YOUTUBE_API_KEY")

def safe_get(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

@app.route("/")
def index():
    keyword = request.args.get("keyword", "")
    growth_filter = request.args.get("growth") == "on"

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

        stats_response = youtube.channels().list(
            part="statistics",
            id=channel_id
        ).execute()

        if stats_response["items"]:
            stats = stats_response["items"][0]["statistics"]
            subs = safe_get(stats.get("subscriberCount"))
            views = safe_get(stats.get("viewCount"))
            video_count = safe_get(stats.get("videoCount"))
            
            months_since_creation = max((datetime.utcnow() - datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")).days / 30, 1)
            estimated_income = (views / months_since_creation) * 0.3

            if not growth_filter or (subs >= 1000 and views >= 10000):
                channels.append({
                    "title": channel_title,
                    "subs": f"{subs:,}",
                    "views": f"{views:,}",
                    "estimated_income": f"{estimated_income:,.0f} 円/月",
                    "published_at": published_at[:10]
                })

    return render_template("index.html", channels=channels, keyword=keyword, growth_filter=growth_filter)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
