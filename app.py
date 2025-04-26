
from flask import Flask, render_template, request
from googleapiclient.discovery import build
from dateutil import parser
import datetime
import os

app = Flask(__name__)
API_KEY = os.environ.get("YOUTUBE_API_KEY")

GENRE_KEYWORDS = {
    "教育": ["勉強", "教育", "学習", "講義", "参考書", "解説", "授業"],
    "エンターテイメント": ["エンタメ", "バラエティ", "ドッキリ", "コント", "ショー", "芸能"],
    "ゲーム": ["ゲーム", "実況", "攻略", "プレイ動画", "対戦", "配信"],
    "ビジネス": ["ビジネス", "副業", "起業", "投資", "企業分析", "マーケティング"],
    "Vlog（日常）": ["vlog", "日常", "旅行", "暮らし", "ルーティン", "お出かけ"],
    "音楽": ["音楽", "歌", "カバー", "演奏", "ライブ", "ピアノ"],
    "スピリチュアル": ["占い", "スピリチュアル", "波動", "ヒーリング", "引き寄せ"],
    "美容・ファッション": ["メイク", "コスメ", "スキンケア", "美容", "コーデ", "ファッション"],
    "食・料理": ["料理", "レシピ", "グルメ", "食べ歩き", "食レポ", "スイーツ"],
    "スポーツ": ["サッカー", "野球", "バスケットボール", "マラソン", "筋トレ"],
    "科学と技術": ["科学", "テクノロジー", "宇宙", "AI", "ロボット", "発明"],
    "自然・アウトドア": ["キャンプ", "登山", "アウトドア", "釣り", "ハイキング", "自然"],
    "子育て・育児": ["子育て", "育児", "赤ちゃん", "ママ", "パパ", "育児日記"],
    "ペット・動物": ["ペット", "犬", "猫", "動物", "うさぎ", "ハムスター"],
    "お金・節約": ["節約", "家計管理", "貯金", "投資信託", "家計簿"],
    "2ch・まとめ": ["2ch", "5ch", "まとめ", "掲示板", "なんJ", "VIP"],
    "専門解説系": ["解説", "レビュー", "比較", "検証", "説明"],
    "懐かし（レトロ）系": ["レトロ", "昭和", "平成初期", "懐かしい"],
    "バイク": ["バイク", "ツーリング", "ライダー", "モトブログ"],
    "オカルト": ["心霊", "怪談", "UFO", "都市伝説", "未確認生物"],
}

def guess_genre(text):
    for genre, keywords in GENRE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                return genre
    return "その他"

@app.route("/")
def index():
    keyword = request.args.get("keyword", "").lower()
    selected_genre = request.args.get("genre", "")
    filter_growth = request.args.get("growth") == "on"

    youtube = build("youtube", "v3", developerKey=API_KEY)
    search_response = youtube.search().list(
        q=keyword,
        part="snippet",
        type="video",
        maxResults=30,
        publishedAfter=(datetime.datetime.utcnow() - datetime.timedelta(days=180)).isoformat("T") + "Z"
    ).execute()

    channels = []
    seen_ids = set()

    for item in search_response.get("items", []):
        channel_id = item["snippet"]["channelId"]
        if channel_id in seen_ids:
            continue
        seen_ids.add(channel_id)

        channel_title = item["snippet"]["channelTitle"]
        video_title = item["snippet"]["title"]
        video_description = item["snippet"].get("description", "")
        genre = guess_genre(video_title + " " + video_description)

        ch_data = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        ).execute()

        if ch_data["items"]:
            ch = ch_data["items"][0]
            published_at = parser.parse(ch["snippet"]["publishedAt"])
            stats = ch["statistics"]
            subs = int(stats.get("subscriberCount", 0))
            views = int(stats.get("viewCount", 0))

            if not filter_growth or (
                (datetime.datetime.utcnow() - published_at.replace(tzinfo=None)).days <= 180 and subs >= 1000 and views >= 10000
            ):
                if (not selected_genre or genre == selected_genre):
                    months_since_creation = max((datetime.datetime.utcnow() - published_at).days / 30, 1)
                    monthly_views = views / months_since_creation
                    estimated_monthly_income = int(monthly_views * 0.3)
                    channels.append({
                        "title": channel_title,
                        "url": f"https://www.youtube.com/channel/{channel_id}",
                        "subscribers": f"{subs:,}",
                        "views": f"{views:,}",
                        "category": genre,
                        "created": published_at.strftime("%Y/%m/%d"),
                        "estimated_income": f"{estimated_monthly_income:,}"
                    })

    return render_template("index.html", channels=channels, genres=GENRE_KEYWORDS.keys(), rivals=len(channels))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
