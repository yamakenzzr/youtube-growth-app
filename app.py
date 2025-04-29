
import os
from flask import Flask, request, render_template, session
from googleapiclient.discovery import build
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)
API_KEY = os.environ.get("YOUTUBE_API_KEY")

GENRES = [
    "教育・解説", "ビジネス・副業", "エンタメ・バラエティ", "Vlog・ライフスタイル",
    "ゲーム・実況", "音楽・歌ってみた", "料理・食べ歩き", "美容・ファッション",
    "スポーツ・トレーニング", "科学・テクノロジー", "ペット・動物",
    "心霊・都市伝説・オカルト", "まとめ・ゆっくり解説", "マンガ・アニメ考察",
    "車・バイク", "子育て・ファミリー", "レトロ・懐かし系"
]

def guess_genre(text):
    text = text.lower()
    genre_keywords = {
        "教育・解説": ["勉強", "解説", "授業", "資格"],
        "ビジネス・副業": ["副業", "投資", "起業"],
        "エンタメ・バラエティ": ["ドッキリ", "バラエティ"],
        "Vlog・ライフスタイル": ["日常", "旅行", "暮らし"],
        "ゲーム・実況": ["ゲーム実況", "攻略"],
        "音楽・歌ってみた": ["歌ってみた", "演奏"],
        "料理・食べ歩き": ["料理", "食べ歩き"],
        "美容・ファッション": ["メイク", "コスメ"],
        "スポーツ・トレーニング": ["筋トレ", "サッカー"],
        "科学・テクノロジー": ["宇宙", "AI"],
        "ペット・動物": ["犬", "猫", "ペット"],
        "心霊・都市伝説・オカルト": ["心霊", "都市伝説"],
        "まとめ・ゆっくり解説": ["ゆっくり解説", "まとめ"],
        "マンガ・アニメ考察": ["考察", "アニメ"],
        "車・バイク": ["車", "バイク"],
        "子育て・ファミリー": ["育児", "子育て"],
        "レトロ・懐かし系": ["レトロ", "昭和"]
    }
    for genre, keywords in genre_keywords.items():
        if any(kw in text for kw in keywords):
            return genre
    return "未分類"

def format_subscribers(subs):
    subs = int(subs)
    if subs >= 100000:
        return f"{subs//10000}万人"
    elif subs >= 10000:
        return f"{subs/10000:.1f}万人"
    else:
        return f"{subs}人"

def format_views(views):
    views = int(views)
    if views >= 100000:
        return f"{views//10000}万回再生"
    elif views >= 10000:
        return f"{views/10000:.1f}万回再生"
    else:
        return f"{views}回再生"

@app.route("/", methods=["GET"])
def index():
    if "search_count" not in session:
        session["search_count"] = 0

    keyword = request.args.get("keyword", "")
    growth_filter = request.args.get("growth_filter", "")
    genre_filter = request.args.get("genre_filter", "")

    channels = []

    if keyword and session["search_count"] < 50:
        youtube = build("youtube", "v3", developerKey=API_KEY)
        search_response = youtube.search().list(
            q=keyword,
            type="video",
            part="snippet",
            maxResults=30
        ).execute()

        seen = set()

        for item in search_response.get("items", []):
            cid = item["snippet"]["channelId"]
            if cid in seen:
                continue
            seen.add(cid)

            channel = youtube.channels().list(part="snippet,statistics", id=cid).execute()
            if channel["items"]:
                ch = channel["items"][0]
                title = ch["snippet"].get("title", "")
                desc = ch["snippet"].get("description", "")
                pub = ch["snippet"].get("publishedAt", "")[:10]
                pub_date = datetime.strptime(pub, "%Y-%m-%d")
                now = datetime.utcnow()
                months = (now.year - pub_date.year) * 12 + now.month - pub_date.month

                if growth_filter == "3" and months > 3:
                    continue
                if growth_filter == "6" and months > 6:
                    continue

                subs = ch["statistics"].get("subscriberCount", 0)
                views = ch["statistics"].get("viewCount", 0)
                genre = guess_genre(title + desc)

                if genre_filter and genre_filter != genre:
                    continue

                channels.append({
                    "title": title,
                    "link": f"https://www.youtube.com/channel/{cid}",
                    "subs": format_subscribers(subs),
                    "views": format_views(views),
                    "published_at": pub,
                    "genre": genre
                })

        session["search_count"] += 1

    return render_template("index.html", channels=channels, keyword=keyword,
                           growth_filter=growth_filter, genre_filter=genre_filter,
                           genres=GENRES, search_count=session["search_count"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
