import os
from flask import Flask, request, render_template
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import math

app = Flask(__name__)

@app.route("/healthz")
def health_check():
    return "Service Running", 200

API_KEY = os.environ.get("YOUTUBE_API_KEY")

def safe_get(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def estimate_category(title):
    """チャンネルタイトルからカテゴリを仮判定する簡易関数"""
    if "占い" in title:
        return "エンターテイメント", "占い"
    elif "バイク" in title:
        return "趣味", "バイク"
    elif "オカルト" in title or "怪談" in title:
        return "エンターテイメント", "オカルト"
    elif "2ch" in title or "スレ" in title:
        return "エンターテイメント", "2chまとめ"
    else:
        return "その他", "その他"

@app.route("/")
def index():
    keyword = request.args.get("keyword", "")
    growth_filter = request.args.get("growth") == "on"

    youtube = build("youtube", "v3", developerKey=API_KEY)

    search_response = youtube.search().list(
        q=keyword,
        type="channel",
        part="snippet",
        maxResults=20,
        publishedAfter=(datetime.utcnow() - timedelta(days=180)).isoformat("T") + "Z"
    ).execute()

    channels = []
    seen_channel_ids = set()

    for item in search_response.get("items", []):
        channel_id = item["snippet"]["channelId"]
        if channel_id in seen_channel_ids:
            continue
        seen_channel_ids.add(channel_id)

        channel_title = item["snippet"]["title"]
        published_at = item["snippet"]["publishedAt"]

        stats_response = youtube.channels().list(
            part="statistics",
            id=channel_id
        ).execute()

        if stats_response["items"]:
            stats = stats_response["items"][0]["statistics"]
            subs = safe_get(stats.get("subscriberCount"))
            views = safe_get(stats.get("viewCount"))

            months_since_creation = max((datetime.utcnow() - datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")).days // 30, 1)
            estimated_income = (views // 1000) * 1.5 // months_since_creation  # 推定月収（単価1.5円/k再生）

            if not growth_filter or (subs >= 1000 and views >= 10000):
                category, genre = estimate_category(channel_title)

                channels.append({
                    "title": channel_title,
                    "link": f"https://www.youtube.com/channel/{channel_id}",
                    "subs": subs,
                    "views": views,
                    "estimated_income": int(estimated_income),
                    "published_at": published_at,
                    "category": category,
                    "genre": genre,
                })

    return render_template("index.html", channels=channels, keyword=keyword, growth_filter=growth_filter)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
