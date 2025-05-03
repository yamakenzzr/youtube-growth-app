import os
from datetime import datetime
from dateutil.parser import parse, timedelta
from flask import Flask, render_template, request, session
from googleapiclient.discovery import build


def safe_parse_date(date_str):
    try:
        clean_str = date_str.split(".")[0] + "Z" if "." in date_str else date_str
        return datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.static_folder = 'static'

API_KEY = os.environ.get("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)

GENRES = [
    "教育・解説", "ビジネス・副業", "ゲーム・実況", "エンタメ・バラエティ",
    "音楽・歌ってみた", "美容・ファッション", "グルメ・料理", "Vlog・ライフスタイル",
    "ママ・育児", "ペット・動物", "スポーツ・筋トレ・健康", "車・バイク・乗り物",
    "占い・スピリチュアル", "作業・DIY・クラフト", "2ch・なんJ系", "本・要約・読書系",
    "メンタル・自己啓発", "映画・アニメ考察", "旅行・観光・絶景", "AI・ツール紹介",
    "恋愛・男女心理", "オカルト・ミステリー", "未分類"
]

genre_keywords = {
    "教育・解説": ["解説", "授業", "教育", "学習", "講座", "入門", "わかりやすく", "学校", "先生", "教科書"],
    "ビジネス・副業": ["副業", "ビジネス", "起業", "稼ぐ", "資産", "収入", "お金", "投資", "株", "マーケティング"],
    "ゲーム・実況": ["ゲーム", "実況", "プレイ", "攻略", "配信", "スプラトゥーン", "マイクラ", "APEX", "FPS", "RPG"],
    "エンタメ・バラエティ": ["バラエティ", "ドッキリ", "お笑い", "芸人", "ネタ", "コント", "番組", "演出", "トーク", "リアクション"],
    "音楽・歌ってみた": ["歌ってみた", "音楽", "カバー", "歌", "弾いてみた", "ライブ", "ボーカル", "ピアノ", "ギター", "アレンジ"],
    "美容・ファッション": ["メイク", "美容", "コスメ", "スキンケア", "化粧", "ヘア", "ファッション", "服", "ネイル", "着こなし"],
    "グルメ・料理": ["料理", "レシピ", "グルメ", "食べてみた", "食べ歩き", "ご飯", "ランチ", "モッパン", "弁当", "食レポ"],
    "Vlog・ライフスタイル": ["Vlog", "日常", "暮らし", "ライフスタイル", "日記", "朝のルーティン", "ナイトルーティン", "一人暮らし", "習慣", "生活"],
    "ママ・育児": ["育児", "子育て", "ママ", "赤ちゃん", "出産", "離乳食", "ベビー", "家庭", "家事", "親子"],
    "ペット・動物": ["犬", "猫", "ペット", "動物", "かわいい", "癒し", "うさぎ", "モルモット", "飼い方", "ペット用品"],
    "スポーツ・筋トレ・健康": ["筋トレ", "健康", "運動", "トレーニング", "ストレッチ", "ヨガ", "ランニング", "ダイエット", "スポーツ", "体づくり", "野球", "サッカー", "バスケ", "テニス", "バレーボール", "卓球"],
    "車・バイク・乗り物": ["車", "バイク", "ドライブ", "ツーリング", "整備", "改造", "レビュー", "自動車", "カスタム", "レース"],
    "占い・スピリチュアル": ["占い", "運勢", "スピリチュアル", "霊視", "タロット", "前世", "引き寄せ", "風水", "星座", "予言"],
    "作業・DIY・クラフト": ["DIY", "クラフト", "作業", "ハンドメイド", "リメイク", "工具", "工作", "修理", "棚作り", "手作り"],
    "2ch・なんJ系": ["2ch", "なんJ", "スレ", "まとめ", "実況スレ", "爆笑", "レス", "コピペ", "掲示板", "ネタ"],
    "本・要約・読書系": ["要約", "読書", "書評", "本", "ビジネス書", "自己啓発本", "図書", "読んでみた", "要点", "ブックレビュー"],
    "メンタル・自己啓発": ["自己啓発", "ポジティブ", "悩み", "メンタル", "幸せ", "心理", "マインドセット", "習慣", "感情", "癒し"],
    "映画・アニメ考察": ["アニメ", "映画", "考察", "レビュー", "解説", "シーン", "伏線", "感想", "ランキング", "作品紹介"],
    "旅行・観光・絶景": ["旅行", "観光", "絶景", "海外", "国内旅行", "旅", "名所", "ツアー", "温泉", "撮影スポット"],
    "AI・ツール紹介": ["AI", "ツール", "使い方", "紹介", "レビュー", "便利", "時短", "効率化", "自動化", "アプリ"],
    "恋愛・男女心理": ["恋愛", "告白", "失恋", "カップル", "心理", "モテる", "男心", "女心", "デート", "復縁"],
    "オカルト・ミステリー": ["オカルト", "ミステリー", "心霊", "怪談", "怖い話", "UFO", "都市伝説", "未解決", "UMA", "陰謀"]
}

def guess_genre(text):
    for genre, keywords in genre_keywords.items():
        if any(keyword.lower() in text.lower() for keyword in keywords):
            return genre
    return "未分類"

@app.route("/")
def index():
    keyword = request.args.get("keyword", "")
    genre_filter = request.args.get("genre", "")
    sort = request.args.get("sort", "views")
    period = request.args.get("period", "")

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    if session.get("search_date") != today_str:
        session["search_count"] = 0
        session["search_date"] = today_str
    session["search_count"] = session.get("search_count", 0) + 1

    results = []
    if keyword and len(keyword) >= 2:
        search_res = youtube.search().list(
            q=keyword, part="snippet", type="channel", maxResults=10
        ).execute()

        channel_ids = [item["snippet"]["channelId"] for item in search_res["items"]]
        details = youtube.channels().list(
            id=",".join(channel_ids), part="snippet,statistics"
        ).execute()

        for ch in details["items"]:
            title = ch["snippet"]["title"]
            desc = ch["snippet"].get("description", "")
            combined = f"{title} {desc}"
            genre = guess_genre(combined)
            if genre_filter and genre_filter != genre:
                continue

            pub_date_str = ch["snippet"].get("publishedAt", "")
            pub_date = safe_parse_date(pub_date_str)
            if period == "3m" and pub_date and pub_date < datetime.utcnow() - timedelta(days=90):
                continue
            if period == "6m" and pub_date and pub_date < datetime.utcnow() - timedelta(days=180):
                continue

            sub = ch["statistics"].get("subscriberCount")
            view = ch["statistics"].get("viewCount")
            video = ch["statistics"].get("videoCount")

            if sub is None:
                sub_display = "非公開"
                ratio_display = "―"
            else:
                sub = int(sub)
                sub_display = f"{sub:,}" if sub > 0 else "0人"
                if view and sub > 0:
                    ratio_display = f"{int(int(view) / sub)}回/人"
                else:
                    ratio_display = "―"

            view_display = f"{int(view):,}回" if view else "非公開"
            icon = ch["snippet"].get("thumbnails", {}).get("default", {}).get("url", "/static/no-image.png")
            published = pub_date_str[:10] if pub_date_str else "不明"

            results.append({
                "id": ch["id"],
                "title": title,
                "subscriberCount": sub_display,
                "viewCount": view_display,
                "videoCount": video if video else "不明",
                "playPerSub": ratio_display,
                "genre": genre,
                "publishedAt": published,
                "icon": icon
            })

    return render_template("index.html", genres=GENRES, keyword=keyword,
                           genre=genre_filter, sort=sort, sort_name=sort,
                           channels=results, period=period)

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/welcome")
def welcome():
    return render_template("welcome.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
