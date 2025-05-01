
import os
from flask import Flask, request, render_template, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

GENRES = [
    "教育・解説", "ビジネス・副業", "ゲーム・実況", "エンタメ・バラエティ",
    "音楽・歌ってみた", "美容・ファッション", "グルメ・料理", "Vlog・ライフスタイル",
    "ママ・育児", "ペット・動物", "スポーツ・筋トレ・健康", "車・バイク・乗り物",
    "占い・スピリチュアル", "作業・DIY・クラフト", "2ch・なんJ", "本・要約・読書系",
    "メンタル・自己啓発", "映画・アニメ考察", "旅行・観光・絶景", "AI・ツール紹介",
    "恋愛・男女心理", "オカルト・ミステリー", "未分類"
]

def guess_genre(text):
    for genre, keywords in {
        "占い・スピリチュアル": ["占い", "霊視", "オーラ", "運勢"],
        "ゲーム・実況": ["ゲーム", "実況", "攻略"],
        "本・要約・読書系": ["読書", "書評", "要約"],
    }.items():
        if any(k in text for k in keywords):
            return genre
    return "未分類"

@app.route("/")
def index():
    keyword = request.args.get("keyword", "")
    genre = request.args.get("genre", "")
    sort = request.args.get("sort", "views")

    if "search_count" not in session:
        session["search_count"] = 0
    session["search_count"] += 1

    data = [
        {
            "id": "UC111", "title": "占いちゃんねる", "subscriberCount": "1万",
            "viewCount": "300万", "videoCount": "100", "publishedAt": "2023-02-01"
        },
        {
            "id": "UC222", "title": "ゲーム配信者Z", "subscriberCount": "5万",
            "viewCount": "1000万", "videoCount": "500", "publishedAt": "2022-05-01"
        }
    ]

    filtered = []
    for ch in data:
        if keyword in ch["title"] and (not genre or guess_genre(ch["title"]) == genre):
            ch["playPerSub"] = "300"
            ch["genre"] = guess_genre(ch["title"])
            filtered.append(ch)

    sort_name = {
        "views": "再生数順",
        "subs": "登録者順",
        "videos": "投稿数順",
        "ratio": "1人あたり再生数順"
    }.get(sort, "再生数順")

    return render_template("index.html", genres=GENRES, keyword=keyword, genre=genre,
                           sort=sort, sort_name=sort_name, channels=filtered)

@app.route("/welcome")
def welcome():
    return render_template("welcome.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
