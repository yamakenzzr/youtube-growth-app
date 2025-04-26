from flask import Flask, render_template, request
from googleapiclient.discovery import build
from datetime import datetime
import os

app = Flask(__name__)

API_KEY = os.environ.get("YOUTUBE_API_KEY")

@app.route('/')
def index():
    keyword = request.args.get("keyword", "")
    growth = request.args.get("growth") == "on"

    youtube = build("youtube", "v3", developerKey=API_KEY)
    search_response = youtube.search().list(
        q=keyword,
        part="snippet",
        type="channel",
        maxResults=20
    ).execute()

    channels = []
    for item in search_response.get("items", []):
        ch_id = item["snippet"]["channelId"]
        ch_title = item["snippet"]["title"]
        ch_data = youtube.channels().list(
            part="statistics,snippet",
            id=ch_id
        ).execute()

        stats = ch_data["items"][0]["statistics"]
        snippet = ch_data["items"][0]["snippet"]
        subs = int(stats.get("subscriberCount", 0))
        views = int(stats.get("viewCount", 0))
        published_at = snippet.get("publishedAt")

        if published_at:
            published_dt = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
            months_since_creation = max((datetime.utcnow() - published_dt).days // 30, 1)
        else:
            months_since_creation = 1

        monthly_estimated_income = (views / months_since_creation / 1000) * 1.5

        channels.append({
            "title": ch_title,
            "subs": subs,
            "views": views,
            "published_at": published_dt.strftime("%Y/%m/%d") if published_at else "不明",
            "monthly_income": f"{int(monthly_estimated_income):,} 円"
        })

    channels = sorted(channels, key=lambda x: x["subs"], reverse=True)

    return render_template("index.html", channels=channels, keyword=keyword, growth=growth)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)