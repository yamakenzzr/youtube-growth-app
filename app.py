from flask import Flask, render_template
from googleapiclient.discovery import build
from dateutil import parser
import datetime

app = Flask(__name__)

API_KEY = "AIzaSyCJqhTmE9qzZrAAtthF2vT-tnYUfVvHdTY"  # あなたのAPIキー

@app.route("/")
def index():
    youtube = build("youtube", "v3", developerKey=API_KEY)

    search_response = youtube.search().list(
        q="教育 OR 解説 OR 勉強",
        part="snippet",
        type="video",
        maxResults=30,
        publishedAfter=(datetime.datetime.utcnow() - datetime.timedelta(days=180)).isoformat("T") + "Z"
    ).execute()

    channels = []

    for item in search_response["items"]:
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

            if (datetime.datetime.utcnow() - published_at).days <= 180 and subs >= 1000 and views >= 10000:
                channels.append({
                    "title": channel_title,
                    "url": f"https://www.youtube.com/channel/{channel_id}",
                    "subscribers": f"{subs:,}",
                    "views": f"{views:,}",
                    "category": "教育",
                    "created": published_at.strftime("%Y/%m/%d")
                })

    return render_template("index.html", channels=channels)
app.run(host="0.0.0.0", port=10000)
