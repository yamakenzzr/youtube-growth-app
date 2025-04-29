
import os
from flask import Flask, request, render_template
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.urandom(24)

API_KEY = os.environ.get("YOUTUBE_API_KEY")

CATEGORY_MAPPING = {
    "1": "映画とアニメ",
    "2": "自動車と乗り物",
    "10": "音楽",
    "15": "ペットと動物",
    "17": "スポーツ",
    "18": "短編映画",
    "19": "旅行とイベント",
    "20": "ゲーム",
    "21": "ブログ",
    "22": "コメディ",
    "23": "エンターテイメント",
    "24": "ニュースと政治",
    "25": "ハウツーとスタイル",
    "26": "教育",
    "27": "科学と技術",
    "28": "非営利・社会活動"
}

def guess_genre(title, description=""):
    text = (title + " " + description).lower()
    genre_keywords = {
        "教育・解説": ["勉強", "学習", "解説", "授業", "資格", "知識", "講座", "受験"],
        "ビジネス・副業": ["副業", "投資", "起業", "経営", "資産運用", "経済", "フリーランス"],
        "エンタメ・バラエティ": ["ドッキリ", "ネタ", "面白い", "検証", "チャレンジ", "バラエティ"],
        "Vlog・ライフスタイル": ["日常", "ルーティン", "暮らし", "旅行", "生活", "カフェ", "観光", "主婦"],
        "ゲーム・実況": ["ゲーム実況", "プレイ動画", "攻略", "配信", "対戦"],
        "音楽・歌ってみた": ["カバー", "歌ってみた", "演奏", "楽器", "作曲", "ライブ"],
        "料理・食べ歩き": ["料理", "レシピ", "クッキング", "食べ歩き", "グルメ", "ラーメン"],
        "美容・ファッション": ["コスメ", "メイク", "スキンケア", "ファッション", "美容", "髪型"],
        "スポーツ・トレーニング": ["筋トレ", "フィットネス", "ダイエット", "サッカー", "野球", "バスケ"],
        "科学・テクノロジー": ["ai", "宇宙", "科学", "ガジェット", "it", "レビュー"],
        "ペット・動物": ["犬", "猫", "ハムスター", "ペット", "動物", "癒し"],
        "心霊・都市伝説・オカルト": ["心霊", "怪談", "都市伝説", "怖い話", "超常現象"],
        "まとめ・ゆっくり解説": ["ゆっくり解説", "2ch", "5ch", "まとめ"],
        "マンガ・アニメ考察": ["考察", "ネタバレ", "アニメ", "漫画", "伏線"],
        "車・バイク": ["ドライブ", "車中泊", "カーライフ", "バイク", "ツーリング"],
        "子育て・ファミリー": ["子育て", "育児", "赤ちゃん", "ママ", "パパ", "家族"],
        "レトロ・懐かし系": ["昭和", "レトロ", "懐かしい", "昔話", "レトロゲーム"]
    }
    for genre, keywords in genre_keywords.items():
        for kw in keywords:
            if kw.lower() in text:
                return genre
    return "未分類"

def format_subscribers(subs):
    if subs >= 100000:
        return f"{subs//10000}万人"
    elif subs >= 10000:
        return f"{subs/10000:.1f}万人"
    else:
        return f"{subs}人"

def format_views(views):
    if views >= 100000:
        return f"{views//10000}万回再生"
    elif views >= 10000:
        return f"{views/10000:.1f}万回再生"
    else:
        return f"{views}回再生"

@app.route("/", methods=["GET"])
def index():
    keyword = request.args.get("keyword", "")
    channels = []

    if keyword:
        youtube = build("youtube", "v3", developerKey=API_KEY)

        search_response = youtube.search().list(
            q=keyword,
            type="video",
            part="snippet",
            maxResults=20
        ).execute()

        seen_channel_ids = set()

        for item in search_response.get("items", []):
            channel_id = item["snippet"]["channelId"]
            if channel_id in seen_channel_ids:
                continue
            seen_channel_ids.add(channel_id)

            channel_response = youtube.channels().list(
                part="snippet,statistics",
                id=channel_id
            ).execute()

            if channel_response["items"]:
                channel = channel_response["items"][0]
                snippet = channel["snippet"]
                statistics = channel["statistics"]

                title = snippet.get("title", "")
                description = snippet.get("description", "")
                published_at = snippet.get("publishedAt", "")[:10]
                subscriber_count = int(statistics.get("subscriberCount", 0))
                view_count = int(statistics.get("viewCount", 0))
                category_id = snippet.get("categoryId", "0")
                category = CATEGORY_MAPPING.get(category_id, "不明")

                genre = guess_genre(title, description)

                channels.append({
                    "title": title,
                    "link": f"https://www.youtube.com/channel/{channel_id}",
                    "subs": format_subscribers(subscriber_count),
                    "views": format_views(view_count),
                    "published_at": published_at,
                    "category": category,
                    "genre": genre
                })

    return render_template("index.html", channels=channels, keyword=keyword)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
