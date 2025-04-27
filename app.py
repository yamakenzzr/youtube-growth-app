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

def format_number(value):
    """数字を万・億単位でわかりやすく整形"""
    if value >= 100000000:
        return f"{value / 100000000:.1f}億"
    elif value >= 10000:
        return f"{value / 10000:.1f}万"
    else:
        return f"{value}"

def guess_genre(title, description=""):
    """チャンネルタイトル・概要文からジャンル推定"""
    text = (title + " " + description).lower()

    genre_keywords = {
        "映画とアニメ": ["映画", "アニメ", "映画レビュー", "アニメ解説"],
        "自動車と乗り物": ["車", "バイク", "乗り物", "ツーリング"],
        "音楽": ["音楽", "演奏", "ピアノ", "歌ってみた", "ライブ"],
        "ペットと動物": ["犬", "猫", "動物", "ハムスター", "ペット"],
        "スポーツ": ["サッカー", "野球", "バスケ", "スポーツ", "マラソン"],
        "旅行とイベント": ["旅行", "観光", "おでかけ", "イベント"],
        "ゲーム": ["ゲーム実況", "ゲーム", "攻略", "プレイ動画"],
        "ブログ": ["Vlog", "日常", "暮らし", "ルーティン"],
        "コメディ": ["コメディ", "ドッキリ", "お笑い"],
        "エンターテイメント": ["バラエティ", "エンタメ", "ネタ動画"],
        "ニュースと政治": ["ニュース", "政治", "時事", "報道"],
        "ハウツーとスタイル": ["ハウツー", "やり方", "スタイル", "DIY"],
        "教育": ["教育", "勉強", "学習", "授業", "参考書"],
        "科学と技術": ["科学", "テクノロジー", "宇宙", "AI"],
        "美容・ファッション": ["メイク", "コスメ", "スキンケア", "ファッション"],
        "スピリチュアル": ["占い", "スピリチュアル", "ヒーリング"],
        "2ch・まとめ": ["2ch", "5ch", "まとめ", "スレ"],
        "Vlog（日常系）": ["Vlog", "日常", "ライフスタイル"],
        "食・料理": ["料理", "レシピ", "グルメ", "食べ歩き"],
        "自然・アウトドア": ["アウトドア", "キャンプ", "登山", "釣り"],
        "子育て・育児": ["子育て", "育児", "ママ", "パパ"],
        "お金・節約": ["節約", "貯金", "家計管理", "投資信託"],
        "専門解説系": ["経済", "法律", "医療", "科学解説"],
        "懐かし（レトロ）系": ["昭和", "レトロ", "懐かしい", "昔話"],
        "バイク": ["バイク", "二輪", "ツーリング"],
        "オカルト": ["オカルト", "怪談", "都市伝説", "心霊"],
    }

    for genre, keywords in genre_keywords.items():
        for kw in keywords:
            if kw in text:
                return genre
    return "その他"

@app.route("/")
def index():
    keyword = request.args.get("keyword", "")
    selected_genre = request.args.get("genre", "")
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
                estimated_monthly_income = (views * 0.3) // months_since_creation
                estimated_total_income = views * 0.3

                genre = guess_genre(channel_title, description)

                if selected_genre and genre != selected_genre:
                    continue

                if not growth_filter or (subs >= 1000 and views >= 10000):
                    channels.append({
                        "title": channel_title,
                        "link": f"https://www.youtube.com/channel/{channel_id}",
                        "subs": format_number(subs),
                        "views": format_number(views),
                        "estimated_monthly_income": format_number(int(estimated_monthly_income)),
                        "estimated_total_income": format_number(int(estimated_total_income)),
                        "published_at": published_at[:10],
                        "genre": genre,
                    })

    return render_template("index.html", channels=channels, keyword=keyword, selected_genre=selected_genre, growth_filter=growth_filter)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
