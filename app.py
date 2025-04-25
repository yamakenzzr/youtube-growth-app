from flask import Flask, render_template, request
from googleapiclient.discovery import build
from dateutil import parser
import datetime

app = Flask(__name__)

API_KEY = "AIzaSyC_9AmdCyM2Q3JyX8KqAes6SV-Gcv9zXyQ"

@app.route("/")
def index():
    keyword = request.args.get("keyword", "教育")
    use_filter = request.args.get("filter") == "on"

    youtube = build("youtube", "v3", developerKey=API_KEY)

    published_after = (datetime.datetime.utcnow() - datetime.timedelta(days=180)).replace(microsecond=0).isoformat() + "Z"

    search_response = youtube.search().list(
        q=keyword,
        part="snippet",
        type="video",
        maxResults=30,
        publishedAfter=published_after
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

            published_within_days = 180
            min_subscribers = 1000
            min_views = 10000

            if use_filter:
                if (
                    (datetime.datetime.utcnow() - published_at.replace(tzinfo=None)).days <= published_within_days
                    and subs >= min_subscribers
                    and views >= min_views
                ):
                    channels.append({
                        "title": channel_title,
                        "url": f"https://www.youtube.com/channel/{channel_id}",
                        "subscribers": f"{subs:,}",
                        "views": f"{views:,}",
                        "category": "推測中",
                        "created": published_at.strftime("%Y/%m/%d")
                    })
            else:
                channels.append({
                    "title": channel_title,
                    "url": f"https://www.youtube.com/channel/{channel_id}",
                    "subscribers": f"{subs:,}",
                    "views": f"{views:,}",
                    "category": "推測中",
                    "created": published_at.strftime("%Y/%m/%d")
                })

    return render_template("index.html", channels=channels, keyword=keyword, use_filter=use_filter)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)