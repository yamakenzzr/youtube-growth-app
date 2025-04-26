from flask import Flask, render_template, request
from googleapiclient.discovery import build
from dateutil import parser
import datetime
import os

app = Flask(__name__)
API_KEY = os.environ.get("YOUTUBE_API_KEY")

@app.route("/")
def index():
    keyword = request.args.get("keyword", "")
    filter_growth = request.args.get("growth") == "on"

    youtube = build("youtube", "v3", developerKey=API_KEY)
    search_response = youtube.search().list(
        q=keyword,
        part="snippet",
        type="video",
        maxResults=30,
        publishedAfter=(datetime.datetime.utcnow() - datetime.timedelta(days=180)).isoformat("T") + "Z"
    ).execute()

    channels = []
    seen_channels = set()

    for item in search_response.get("items", []):
        channel_id = item["snippet"]["channelId"]
        channel_title = item["snippet"]["channelTitle"]

        if channel_id in seen_channels:
            continue
        seen_channels.add(channel_id)

        ch_data = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        ).execute()

        if ch_data["items"]:
            ch = ch_data["items"][0]
            published_at = parser.parse(ch["snippet"]["publishedAt"])
            stats = ch["statistics"]
            subs = int(stats.get("subscriberCount", 0))
            views = int(stats.get("viewCount", 0))

            if not filter_growth or ((datetime.datetime.utcnow() - published_at.replace(tzinfo=None)).days <= 180 and subs >= 1000 and views >= 10000):
                channels.append({
                    "title": channel_title,
                    "url": f"https://www.youtube.com/channel/{channel_id}",
                    "subscribers": f"{subs:,}",
                    "views": f"{views:,}",
                    "category": "推測中",
                    "created": published_at.strftime("%Y/%m/%d")
                })

    return render_template("index.html", channels=channels)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
