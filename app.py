import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = os.urandom(24)
API_KEY = os.environ.get("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)

GENRES = [
    "教育・解説", "ビジネス・副業", "ゲーム・実況", "エンタメ・バラエティ",
    "音楽・歌ってみた", "美容・ファッション", "グルメ・料理", "Vlog・ライフスタイル",
    "ママ・育児", "ペット・動物", "スポーツ・筋トレ・健康", "車・バイク・乗り物",
    "占い・スピリチュアル", "作業・DIY・クラフト", "2ch・なんJ", "本・要約・読書系",
    "メンタル・自己啓発", "映画・アニメ考察", "旅行・観光・絶景", "AI・ツール紹介",
    "恋愛・男女心理", "オカルト・ミステリー", "未分類"
]

def format_japanese_number(value):
    try:
        value = int(value)
        if value >= 100_000_000:
            return f"{value / 100_000_000:.1f}億"
        elif value >= 10_000:
            return f"{value / 10_000:.1f}万"
        else:
            return str(value)
    except:
        return str(value)

def guess_genre(text):
    genre_keywords = {
        "占い・スピリチュアル": ["占い", "スピリチュアル", "運勢", "霊視", "タロット"],
        "ゲーム・実況": ["ゲーム", "実況", "プレイ", "攻略", "Switch", "PS5"],
        "スポーツ・筋トレ・健康": ["筋トレ", "フィットネス", "運動", "サッカー", "野球", "健康"],
        "オカルト・ミステリー": ["心霊", "オカルト", "怪談", "ミステリー", "怖い話"],
        "ビジネス・副業": ["副業", "ビジネス", "投資", "稼ぐ", "仕事術"],
        "教育・解説": ["解説", "勉強", "教育", "入門", "講義"],
        "音楽・歌ってみた": ["歌ってみた", "カバー", "ボカロ", "演奏", "ピアノ"],
        "美容・ファッション": ["メイク", "スキンケア", "美容", "コーデ", "ファッション"],
        "グルメ・料理": ["レシピ", "料理", "グルメ", "食べ歩き", "自炊"],
        "Vlog・ライフスタイル": ["Vlog", "ルーティン", "ライフスタイル", "暮らし"],
        "ママ・育児": ["子育て", "ママ", "育児", "赤ちゃん"],
        "ペット・動物": ["犬", "猫", "ペット", "動物"],
        "車・バイク・乗り物": ["車", "バイク", "ドライブ", "モータースポーツ"],
        "作業・DIY・クラフト": ["DIY", "作業", "ハンドメイド", "クラフト"],
        "本・要約・読書系": ["書評", "要約", "読書", "本"],
        "メンタル・自己啓発": ["メンタル", "自己啓発", "心理学", "前向き", "悩み"],
        "映画・アニメ考察": ["考察", "映画", "アニメ", "伏線", "解説"],
        "旅行・観光・絶景": ["旅行", "観光", "絶景", "旅"],
        "AI・ツール紹介": ["AI", "ツール", "自動化", "ChatGPT", "便利アプリ"],
        "恋愛・男女心理": ["恋愛", "心理", "モテ", "恋", "男女"],
        "2ch・なんJ": ["2ch", "なんJ", "スレ", "まとめ"]
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
            video = int(ch["statistics"].get("videoCount", 0))
            ratio = int(view / sub) if sub > 0 else 0

            results.append({
                "id": ch["id"], "title": title,
                "subscriberCount": format_japanese_number(sub) + "人",
                "viewCount": format_japanese_number(view) + "回",
                "videoCount": format_japanese_number(video) + "本",
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