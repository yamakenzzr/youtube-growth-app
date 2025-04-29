from flask import Flask, render_template, request
import os
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = os.environ.get("YOUTUBE_API_KEY")

def calculate_estimated_income(views_last_month):
    rpm = 1.5  # 仮定のYouTube RPM（1再生あたりの収益）
    return int(views_last_month * rpm / 1000)

@app.route("/", methods=["GET"])
def index():
    keyword = request.args.get("keyword", "")
    filter_growth = request.args.get("growth", "off") == "on"

    channels = []

    if keyword and API_KEY:
        youtube = build("youtube", "v3", developerKey=API_KEY)
        now = datetime.utcnow()
        published_after = (now - timedelta(days=180)).isoformat("T") + "Z"

        search_response = youtube.search().list(
            q=keyword,
            part="snippet",
            type="channel",
            maxResults=20,
            order="date",
            publishedAfter=published_after
        ).execute()

        channel_ids = [item["snippet"]["channelId"] for item in search_response.get("items", [])]

        if channel_ids:
            channels_response = youtube.channels().list(
                part="snippet,statistics",
                id=",".join(channel_ids)
            ).execute()

            seen_channel_ids = set()
            for item in channels_response.get("items", []):
                channel_id = item["id"]
                if channel_id in seen_channel_ids:
                    continue
                seen_channel_ids.add(channel_id)

                snippet = item["snippet"]
                stats = item["statistics"]
                published_at = datetime.strptime(snippet.get("publishedAt", ""), "%Y-%m-%dT%H:%M:%SZ")

                subs = int(stats.get("subscriberCount", 0))
                views = int(stats.get("viewCount", 0))

                months_since_creation = max((now - published_at).days / 30, 1)
                views_per_month = views / months_since_creation
                estimated_income = calculate_estimated_income(views_per_month)

                if filter_growth:
                    if (now - published_at).days > 180 or subs < 1000 or views < 10000:
                        continue

                channels.append({
                    "title": snippet.get("title", "不明"),
                    "subs": f"{subs:,}",
                    "views": f"{views:,}",
                    "income": f"{estimated_income:,} 円/月",
                    "created_at": published_at.strftime("%Y/%m/%d")
                })

    return render_template("index.html", channels=channels, keyword=keyword, filter_growth=filter_growth)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
