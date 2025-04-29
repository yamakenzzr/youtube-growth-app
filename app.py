import os
from flask import Flask, request, render_template
from googleapiclient.discovery import build
from datetime import datetime, timedelta

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
    """チャンネルタイトルからカテゴリを仮判定する関数"""
    title = title.lower()
    if "占い" in title:
        return "エンタメ"
    elif "バイク" in title:
        return "趣味・バイク"
    elif "オカルト" in title or "怪談" in title:
        return "エンタメ・オカルト"
    elif "2ch" in title or "スレ" in title:
        return "まとめ系"
    else:
        return "その他"

def guess_genre(title, description=""):
    """チャンネル名や概要文からジャンルを推定する簡易関数"""
    text = (title + " " + description).lower()

    genre_keywords = {
        "教育": ["学習", "勉強", "受験", "資格", "講座"],
        "ビジネス": ["投資", "副業", "資産", "経済", "起業"],
        "レトロ": ["昭和", "レトロ", "懐かし", "昔話", "懐古"],
        "バイク": ["バイク", "ツーリング", "二輪"],
        "オカルト": ["怪談", "心霊", "都市伝説", "オカルト", "怖い話"],
        "ゲーム実況": ["ゲーム実況", "プレイ動画", "攻略"],
        "音楽": ["作業用bgm", "演奏", "ギター", "ピアノ"],
        "旅行": ["旅行", "観光", "おでかけ"],
        "料理": ["レシピ", "料理", "クッキング"],
        "2chまとめ": ["2ch", "スレ", "まとめ"],
    }

    for genre, keywords in genre_keywords.items():
        for kw in keywords:
            if kw in text:
                return genre
    return "未分類"

@app.route("/")
def index():
    keyword = request.args.get("keyword", "")
    growth_filter = request.args.get("growth") == "on"

    youtube = build("youtube", "v3", developerKey=API_KEY)

    channels = []
    seen_channel_ids = set()

    if keyword:
        search_response = youtube.search().list(
            q=keyword,
            type="channel",
            part="snippet",
            maxResults=20,
            publishedAfter=(datetime.utcnow() - timedelta(days=180)).isoformat("T") + "Z"
        ).execute()

        for item in search_response.get("items", []):
            channel_id = item["snippet"]["channelId"]
            if channel_id in seen_channel_ids:
                continue
            seen_channel_ids.add(channel_id)

            channel_title = item["snippet"]["title"]
            published_at = item["snippet"]["publishedAt"]

            stats_response = youtube.channels().list(
                part="statistics,snippet",
                id=channel_id
            ).execute()

            if stats_response["items"]:
                stats = stats_response["items"][0]["statistics"]
                snippet = stats_response["items"][0]["snippet"]
                subs = safe_get(stats.get("subscriberCount"))
                views = safe_get(stats.get("viewCount"))
                description = snippet.get("description", "")

                months_since_creation = max((datetime.utcnow() - datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")).days // 30, 1)
                estimated_income = (views // 1000) * 1.5 // months_since_creation  # 推定月収

                if not growth_filter or (subs >= 1000 and views >= 10000):
                    category = estimate_category(channel_title)
                    genre = guess_genre(channel_title, description)

                    channels.append({
                        "title": channel_title,
                        "link": f"https://www.youtube.com/channel/{channel_id}",
                        "subs": subs,
                        "views": views,
                        "estimated_income": int(estimated_income),
                        "published_at": published_at[:10],
                        "category": category,
                        "genre": genre,
                    })

    return render_template("index.html", channels=channels, keyword=keyword, growth_filter=growth_filter)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
