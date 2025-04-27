import os
from flask import Flask, request, render_template
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = os.environ.get("YOUTUBE_API_KEY")

def safe_get(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

ジャンルキーワード = {
    "映画とアニメ": ["映画", "アニメ", "シネマ", "フィルム"],
    "自動車と乗り物": ["車", "バイク", "自動車", "乗り物"],
    "音楽": ["音楽", "歌ってみた", "カバー", "演奏", "ライブ", "ピアノ"],
    "ペットと動物": ["ペット", "犬", "猫", "動物", "うさぎ", "ハムスター"],
    "スポーツ": ["サッカー", "野球", "バスケ", "マラソン", "筋トレ"],
    "旅行とイベント": ["旅行", "観光", "旅", "ツアー", "イベント"],
    "ゲーム": ["ゲーム", "実況", "攻略", "プレイ動画", "配信"],
    "ブログ": ["vlog", "日常", "暮らし", "お出かけ"],
    "コメディ": ["コメディ", "バラエティ", "お笑い", "ドッキリ"],
    "エンターテイメント": ["エンタメ", "エンターテイメント", "パフォーマンス"],
    "ニュースと政治": ["ニュース", "政治", "社会問題", "時事"],
    "ハウツーとスタイル": ["ハウツー", "DIY", "ライフハック", "スタイル"],
    "教育": ["勉強", "教育", "学習", "講義", "授業", "参考書"],
    "科学と技術": ["科学", "テクノロジー", "宇宙", "AI", "ロボット"],
    "美容・ファッション": ["メイク", "コスメ", "スキンケア", "美容", "ファッション"],
    "スピリチュアル": ["占い", "スピリチュアル", "波動", "ヒーリング", "引き寄せ"],
    "2ch・まとめ": ["2ch", "5ch", "まとめ", "掲示板", "なんJ", "VIP"],
    "Vlog": ["Vlog", "ルーティン", "日常", "暮らし"],
    "食・料理": ["料理", "レシピ", "グルメ", "食べ歩き", "食レポ"],
    "自然・アウトドア": ["キャンプ", "登山", "釣り", "アウトドア", "自然"],
    "子育て・育児": ["子育て", "育児", "赤ちゃん", "ママ", "パパ"],
    "お金・節約": ["節約", "家計管理", "貯金", "投資信託"],
    "専門解説系": ["解説", "レビュー", "検証", "比較", "まとめ"],
    "懐かし（レトロ）系": ["レトロ", "昭和", "昔", "懐かし"],
    "バイク": ["バイク", "ツーリング", "モトブログ"],
    "オカルト": ["オカルト", "都市伝説", "心霊", "ホラー"],
}

def estimate_genre(title):
    for genre, keywords in ジャンルキーワード.items():
        for keyword in keywords:
            if keyword.lower() in title.lower():
                return genre
    return "その他"

@app.route("/")
def index():
    keyword = request.args.get("keyword", "")
    genre_filter = request.args.get("genre", "")
    growth_filter = request.args.get("growth", "") == "on"
    channels = []

    if keyword:
        youtube = build("youtube", "v3", developerKey=API_KEY)
        search_response = youtube.search().list(
            q=keyword,
            type="channel",
            part="snippet",
            maxResults=20,
            publishedAfter=(datetime.utcnow() - timedelta(days=180)).isoformat("T") + "Z"
        ).execute()

        seen_channel_ids = set()

        for item in search_response.get("items", []):
            channel_id = item["snippet"]["channelId"]
            if channel_id in seen_channel_ids:
                continue
            seen_channel_ids.add(channel_id)

            channel_title = item["snippet"]["title"]
            published_at = item["snippet"]["publishedAt"]

            stats_response = youtube.channels().list(
                part="statistics",
                id=channel_id
            ).execute()

            if stats_response.get("items"):
                stats = stats_response["items"][0]["statistics"]
                subs = safe_get(stats.get("subscriberCount"))
                views = safe_get(stats.get("viewCount"))
                videos = safe_get(stats.get("videoCount"))

                months_since_creation = max((datetime.utcnow() - datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")).days / 30, 1)
                estimated_income = int(views * 0.15 / months_since_creation)
                estimated_total_income = int(views * 0.15)

                category = "まとめ系" if "2ch" in channel_title or "まとめ" in channel_title else "その他"
                genre = estimate_genre(channel_title)

                if not genre_filter or genre_filter == genre:
                    if not growth_filter or (subs >= 1000 and views >= 100000):
                        channels.append({
                            "title": channel_title,
                            "id": channel_id,
                            "subs": subs,
                            "views": views,
                            "estimated_income": estimated_income,
                            "estimated_total_income": estimated_total_income,
                            "published_at": published_at,
                            "category": category,
                            "genre": genre
                        })

    return render_template("index.html", channels=channels, keyword=keyword, growth_filter=growth_filter, genre_filter=genre_filter)

@app.route("/healthz")
def health_check():
    return "Service Running", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
