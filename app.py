from flask import Flask, render_template, request
from googleapiclient.discovery import build
from dateutil import parser
import datetime

app = Flask(__name__)

API_KEY = "AIzaSyCJqhTmE9qzZrAAtthF2vT-tnYUfVvHdTY"

@app.route("/")
def index():
    keyword = request.args.get("keyword", "教育")

    youtube = build("youtube", "v3", developerKey=API_KEY)

    search_response = youtube.search().list(
        q=keyword,
        part="snippet",
        type="video",
        maxResults=30,
        publishedAfter=(datetime.datetime.utcnow() - datetime.timedelta(days=365)).isoformat("T") + "Z"
    ).execute()

    channels = []
    seen_channel_ids = set()

    for item in search_response["items"]:
        channel_id = item["snippet"]["channelId"]
        channel_title = item["snippet"]["channelTitle"]

        if channel_id in seen_channel_ids:
            continue
        seen_channel_ids.add(channel_id)

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

            if (datetime.datetime.utcnow() - published_at.replace(tzinfo=None)).days <= 365 and subs >= 100 and views >= 1000:
                channels.append({
                    "title": channel_title,
                    "url": f"https://www.youtube.com/channel/{channel_id}",
                    "subscribers": f"{subs:,}",
                    "views": f"{views:,}",
                    "category": "推測中",
                    "created": published_at.strftime("%Y/%m/%d")
                })

    return render_template("index.html", channels=channels, keyword=keyword)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)