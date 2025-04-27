import os
import math
from flask import Flask, request, render_template
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/healthz')
def health_check():
    return "Service Running", 200

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

    channels = []

    if keyword:  # ★キーワードがあるときだけ検索する！
        youtube = build("youtube", "v3", developerKey=API_KEY)
        search_response = youtube.search().list(
            q=keyword,
            type="channel",
            part="snippet",
            maxResults=20,
            publishedAfter=(datetime.utcnow() - timedelta(days=180)).isoformat("T") + "Z"
        ).execute()

        seen_channel_ids = set()

        for item in search_response.get("items", []):
            channel_id = item["snippet"]["channelId"]
            channel_title = item["snippet"]["title"]
            published_at = item["snippet"]["publishedAt"]

            if channel_id in seen_channel_ids:
                continue
            seen_channel_ids.add(channel_id)

            ch_data = youtube.channels().list(
                part="statistics",
                id=channel_id
            ).execute()

            if ch_data["items"]:
                stats = ch_data["items"][0]["statistics"]
                subs = safe_get(stats.get("subscriberCount"))
                views = safe_get(stats.get("viewCount"))

                months_since_creation = max((datetime.utcnow() - datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")).days // 30, 1)
                estimated_income = (views / months_since_creation) * 0.0005

                if not growth_filter or (subs >= 1000 and views >= 10000):
                    channels.append({
                        "title": channel_title,
                        "subs": subs,
                        "views": views,
                        "estimated_income": f"{estimated_income:.0f}",
                        "published_at": published_at
                    })

    return render_template("index.html", channels=channels, keyword=keyword, growth_filter=growth_filter)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
