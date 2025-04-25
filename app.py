
from flask import Flask, render_template, request
from googleapiclient.discovery import build
import datetime
from dateutil import parser
import os

app = Flask(__name__)

API_KEY = os.getenv("YOUTUBE_API_KEY", "YOUR_API_KEY_HERE")

@app.route("/", methods=["GET"])
def index():
    query = request.args.get("q", "")
    youtube = build("youtube", "v3", developerKey=API_KEY)

    published_after = (datetime.datetime.utcnow() - datetime.timedelta(days=180)).replace(microsecond=0).isoformat() + "Z"
    
    search_response = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=30,
        publishedAfter=published_after
    ).execute()

    channels = []
    for item in search_response.get("items", []):
        channel_id = item["snippet"]["channelId"]
        channel_title = item["snippet"]["channelTitle"]

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

            if (datetime.datetime.utcnow() - published_at.replace(tzinfo=None)).days <= 180 and subs >= 1000 and views >= 10000:
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
    app.run(host="0.0.0.0", port=10000)
