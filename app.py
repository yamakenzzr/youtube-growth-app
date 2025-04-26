from flask import Flask, render_template, request
from googleapiclient.discovery import build
from datetime import datetime
import os

app = Flask(__name__)
API_KEY = os.environ.get("YOUTUBE_API_KEY")

@app.route('/')
def index():
    keyword = request.args.get("keyword", "")
    youtube = build("youtube", "v3", developerKey=API_KEY)
    search_response = youtube.search().list(
        q=keyword,
        part="snippet",
        type="channel",
        maxResults=20
    ).execute()

    channels = []
    now = datetime.utcnow()
    for item in search_response.get("items", []):
        channel_id = item["snippet"]["channelId"]
        channel_title = item["snippet"]["title"]
        ch_data = youtube.channels().list(
            part="statistics,snippet",
            id=channel_id
        ).execute()

        if ch_data["items"]:
            snippet = ch_data["items"][0]["snippet"]
            stats = ch_data["items"][0]["statistics"]
            subs = int(stats.get("subscriberCount", 0))
            views = int(stats.get("viewCount", 0))
            published_at = snippet.get("publishedAt")
            if published_at:
                published_dt = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                months = max((now - published_dt).days / 30, 1)
            else:
                months = 1

            estimated_income = int((views / months / 1000) * 1.5)

            channels.append({
                "title": channel_title,
                "subs": subs,
                "views": views,
                "published_at": published_dt.strftime("%Y/%m/%d") if published_at else "不明",
                "estimated_income": f"{estimated_income:,} 円/月"
            })

    return render_template("index.html", channels=channels, keyword=keyword)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)