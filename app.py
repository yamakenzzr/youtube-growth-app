
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = os.urandom(24)
API_KEY = os.environ.get("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)

GENRES = ["占い・スピリチュアル", "ゲーム・実況", "スポーツ・筋トレ・健康", "オカルト・ミステリー", "未分類"]

def guess_genre(text):
    genre_keywords = {
        "占い・スピリチュアル": ["占い", "運勢", "スピリチュアル", "霊視"],
        "ゲーム・実況": ["ゲーム", "実況", "攻略", "プレイ"],
        "スポーツ・筋トレ・健康": ["筋トレ", "運動", "健康", "サッカー", "野球"],
        "オカルト・ミステリー": ["オカルト", "心霊", "ミステリー", "怪談"],
    }
    for genre, keywords in genre_keywords.items():
        if any(k in text for k in keywords):
            return genre
    return "未分類"

@app.route("/")
def index():
    keyword = request.args.get("keyword", "")
    genre_filter = request.args.get("genre", "")
    sort = request.args.get("sort", "views")
    period = request.args.get("period", "")

    if len(keyword.strip()) < 2:
        return render_template("index.html", genres=GENRES, keyword=keyword, genre=genre_filter,
                               sort=sort, sort_name="未設定", channels=[], period=period)

    if "search_count" not in session:
        session["search_count"] = 0
    session["search_count"] += 1

    published_after = None
    if period == "3m":
        published_after = (datetime.utcnow() - timedelta(days=90)).isoformat("T") + "Z"
    elif period == "6m":
        published_after = (datetime.utcnow() - timedelta(days=180)).isoformat("T") + "Z"

    results = []
    search_res = youtube.search().list(
        q=keyword, part="snippet", type="channel", maxResults=10,
        publishedAfter=published_after if published_after else None
    ).execute()

    channel_ids = [item["snippet"]["channelId"] for item in search_res["items"]]
    if channel_ids:
        details = youtube.channels().list(
            id=",".join(channel_ids),
            part="snippet,statistics"
        ).execute()

        for ch in details["items"]:
            title = ch["snippet"]["title"]
            genre = guess_genre(title)
            if genre_filter and genre_filter != genre:
                continue
            sub = int(ch["statistics"].get("subscriberCount", 0))
            view = int(ch["statistics"].get("viewCount", 0))
            ratio = int(view / sub) if sub > 0 else 0

            results.append({
                "id": ch["id"], "title": title,
                "subscriberCount": f"{sub:,}",
                "viewCount": f"{view:,}",
                "videoCount": ch["statistics"].get("videoCount", "不明"),
                "playPerSub": ratio,
                "genre": genre,
                "publishedAt": ch["snippet"]["publishedAt"][:10],
                "icon": ch["snippet"]["thumbnails"]["default"]["url"]
            })

    sort_name = {
        "views": "再生数順", "subs": "登録者順",
        "videos": "投稿数順", "ratio": "1人あたり再生数順"
    }.get(sort, "再生数順")

    return render_template("index.html", genres=GENRES, keyword=keyword, genre=genre_filter,
                           sort=sort, sort_name=sort_name, channels=results, period=period)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
