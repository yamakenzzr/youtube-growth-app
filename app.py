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
        maxResults=20,
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
            published_at = parser.parse(ch_data["items"][0]["snippet"]["publishedAt"])
            stats = ch_data["items"][0]["statistics"]
            subs = int(stats.get("subscriberCount", 0))
            views = int(stats.get("viewCount", 0))
            videos = int(stats.get("videoCount", 1))

            if not filter_growth or ((datetime.datetime.utcnow() - published_at).days <= 180 and subs >= 1000 and views >= 10000):
                months_since_creation = max((datetime.datetime.utcnow() - published_at).days / 30, 1)
                est_income = round((views / months_since_creation) * 0.1)  # 収益推定式

                channels.append({
                    "title": channel_title,
                    "subs": subs,
                    "views": views,
                    "created": published_at.date(),
                    "income": est_income
                })

    channels.sort(key=lambda x: x["subs"], reverse=True)
    return render_template("index.html", channels=channels, keyword=keyword, filter_growth=filter_growth)