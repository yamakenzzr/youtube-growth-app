from flask import Flask, render_template, request
from googleapiclient.discovery import build
from dateutil import parser
import datetime
import os

app = Flask(__name__)
API_KEY = os.environ.get("YOUTUBE_API_KEY")

GENRE_KEYWORDS = {
    "教育": ["勉強", "教育", "学習", "講義", "参考書", "解説"],
    "エンタメ": ["エンタメ", "バラエティ", "お笑い", "ドッキリ", "コント"],
    "ゲーム": ["ゲーム", "実況", "攻略", "プレイ動画"],
    "ビジネス": ["ビジネス", "副業", "起業", "投資", "企業分析"],
    "Vlog": ["vlog", "日常", "旅行", "暮らし", "ルーティン"],
    "音楽": ["音楽", "歌ってみた", "カバー", "演奏", "ピアノ"],
    "スピリチュアル": ["占い", "スピリチュアル", "波動", "ヒーリング", "引き寄せ"],
}

def guess_genre(text):
    for genre, keywords in GENRE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                return genre
    return "その他"

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
    seen_ids = set()

    for item in search_response.get("items", []):
        channel_id = item["snippet"]["channelId"]
        if channel_id in seen_ids:
            continue
        seen_ids.add(channel_id)

        channel_title = item["snippet"]["channelTitle"]
        video_title = item["snippet"]["title"]
        video_description = item["snippet"].get("description", "")

        genre = guess_genre(video_title + " " + video_description)

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

            if not filter_growth or (
                (datetime.datetime.utcnow() - published_at.replace(tzinfo=None)).days <= 180 and subs >= 1000 and views >= 10000
            ):
                channels.append({
                    "title": channel_title,
                    "url": f"https://www.youtube.com/channel/{channel_id}",
                    "subscribers": f"{subs:,}",
                    "views": f"{views:,}",
                    "category": genre,
                    "created": published_at.strftime("%Y/%m/%d")
                })

    return render_template("index.html", channels=channels)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
