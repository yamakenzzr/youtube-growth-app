
import os
from flask import Flask, request, render_template, session
from datetime import datetime
from dateutil.parser import parse

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

@app.route("/")
def index():
    keyword = request.args.get("keyword", "")
    genre = request.args.get("genre", "")
    sort = request.args.get("sort", "views")

    # 仮データで表示テスト（API実行なし）
    dummy_channels = []
    if keyword or genre:
        dummy_channels = [
            {
                "id": "UCXXXXX1",
                "title": "サンプルチャンネルA",
                "subscriberCount": "3.2万",
                "viewCount": "2297.6万",
                "videoCount": "2140",
                "playPerSub": "722",
                "genre": genre if genre else "未分類",
                "publishedAt": "2020-03-19"
            },
            {
                "id": "UCXXXXX2",
                "title": "サンプルチャンネルB",
                "subscriberCount": "4.1万",
                "viewCount": "1629.1万",
                "videoCount": "1489",
                "playPerSub": "393",
                "genre": genre if genre else "未分類",
                "publishedAt": "2019-07-03"
            }
        ]

    sort_name = {
        "views": "再生数順",
        "subs": "登録者順",
        "videos": "投稿数順",
        "ratio": "1人あたり再生数順"
    }.get(sort, "再生数順")

    return render_template("index.html",
        genres=GENRES,
        keyword=keyword,
        genre=genre,
        sort=sort,
        sort_name=sort_name,
        channels=dummy_channels
    )

@app.route("/terms")
def terms():
    return render_template("terms.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
