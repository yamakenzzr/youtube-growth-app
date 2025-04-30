
import os
from flask import Flask, request, render_template, session
from googleapiclient.discovery import build
from datetime import datetime, timezone
from dateutil.parser import parse

app = Flask(__name__)
app.secret_key = os.urandom(24)
API_KEY = os.environ.get("YOUTUBE_API_KEY")

GENRES = [
    "教育・解説", "ビジネス・副業", "ゲーム・実況", "エンタメ・バラエティ",
    "音楽・歌ってみた", "美容・ファッション", "グルメ・料理", "Vlog・ライフスタイル",
    "ママ・育児", "ペット・動物", "スポーツ・筋トレ・健康", "車・バイク・乗り物",
    "占い・スピリチュアル", "作業・DIY・クラフト", "2ch・なんJ", "未分類"
]

GENRE_KEYWORDS = {
    "教育・解説": ["解説", "勉強", "授業", "知識", "学ぶ", "講義", "教養"],
    "ビジネス・副業": ["副業", "稼ぐ", "投資", "起業", "収益", "フリーランス", "資産"],
    "ゲーム・実況": ["ゲーム", "実況", "プレイ", "攻略", "配信", "eスポーツ"],
    "エンタメ・バラエティ": ["バラエティ", "お笑い", "ネタ", "ドッキリ", "面白い", "企画"],
    "音楽・歌ってみた": ["歌ってみた", "カバー", "演奏", "ギター", "ピアノ", "作曲", "ボカロ", "音楽"],
    "美容・ファッション": ["美容", "メイク", "スキンケア", "コスメ", "ファッション", "スタイル", "髪型"],
    "グルメ・料理": ["料理", "レシピ", "グルメ", "モッパン", "食レポ", "食べてみた", "スイーツ"],
    "Vlog・ライフスタイル": ["Vlog", "暮らし", "ルーティン", "日常", "丁寧な暮らし", "ライフスタイル"],
    "ママ・育児": ["育児", "子育て", "ママ", "ベビー", "出産", "離乳食"],
    "ペット・動物": ["ペット", "犬", "猫", "うさぎ", "ハムスター", "動物", "癒し"],
    "スポーツ・筋トレ・健康": ["筋トレ", "ストレッチ", "健康", "運動", "ダイエット", "フィットネス", "体操"],
    "車・バイク・乗り物": ["車", "バイク", "ドライブ", "カスタム", "乗り物", "交通", "モビリティ", "鉄道"],
    "占い・スピリチュアル": ["占い", "スピリチュアル", "タロット", "波動", "宇宙", "霊視"],
    "作業・DIY・クラフト": ["DIY", "修理", "クラフト", "作業", "レザークラフト", "ハンドメイド", "工具"],
    "2ch・なんJ": ["2ch", "なんJ", "なんでも実況", "スレ", "掲示板", "まとめ", "にちゃんねる"]
}

def guess_genre(text):
    for genre, keywords in GENRE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return genre
    return "未分類"

def format_subscribers(subs):
    subs = int(subs)
    if subs >= 100_000_000:
        return f"{subs / 100_000_000:.2f}億人"
    elif subs >= 10_000:
        return f"{subs / 10_000:.1f}万人"
    else:
        return f"{subs}人"

def format_views(views):
    views = int(views)
    if views >= 100_000_000:
        return f"{views / 100_000_000:.2f}億回再生"
    elif views >= 10_000:
        return f"{views / 10_000:.1f}万回再生"
    else:
        return f"{views}回再生"

def format_videos(count):
    count = int(count)
    if count >= 10_000:
        return f"{count / 10000:.1f}万本"
    else:
        return f"{count}本"

def format_ratio(views, subs):
    try:
        ratio = int(views) // int(subs)
        return f"{ratio}回/人"
    except:
        return "N/A"

@app.route("/", methods=["GET"])
def index():
    if "search_count" not in session:
        session["search_count"] = 0

    keyword = request.args.get("keyword", "")
    growth_filter = request.args.get("growth_filter", "")
    genre_filter = request.args.get("genre_filter", "")
    sort_by = request.args.get("sort_by", "views")
    error = None
    channels = []
    blocked = False

    if keyword:
        if len(keyword.strip()) < 2:
            error = "検索ワードは2文字以上で入力してください。"
        elif session["search_count"] < 50:
            youtube = build("youtube", "v3", developerKey=API_KEY)
            search_response = youtube.search().list(
                q=keyword,
                type="video",
                part="snippet",
                maxResults=30
            ).execute()

            seen = set()
            today = datetime.now(timezone.utc)

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
                    pub_raw = ch["snippet"].get("publishedAt", "")
                    try:
                        pub_dt = parse(pub_raw).replace(tzinfo=timezone.utc)
                    except Exception:
                        continue
                    days_since_creation = (today - pub_dt).days

                    if growth_filter == "3" and days_since_creation > 90:
                        continue
                    elif growth_filter == "6" and days_since_creation > 180:
                        continue

                    stats = ch["statistics"]
                    subs = stats.get("subscriberCount", 0)
                    views = stats.get("viewCount", 0)
                    videos = stats.get("videoCount", 0)
                    ratio = format_ratio(views, subs)
                    genre = guess_genre(title + desc)

                    if genre_filter and genre != genre_filter:
                        continue

                    channels.append({
                        "title": title,
                        "link": f"https://www.youtube.com/channel/{cid}",
                        "subs": format_subscribers(subs),
                        "views": format_views(views),
                        "videos": format_videos(videos),
                        "ratio": ratio,
                        "published_at": pub_dt.strftime("%Y-%m-%d"),
                        "genre": genre,
                        "raw_views": int(views),
                        "raw_subs": int(subs),
                        "raw_videos": int(videos)
                    })

            if sort_by == "subs":
                channels.sort(key=lambda ch: ch["raw_subs"], reverse=True)
            elif sort_by == "videos":
                channels.sort(key=lambda ch: ch["raw_videos"], reverse=True)
            else:
                channels.sort(key=lambda ch: ch["raw_views"], reverse=True)

            session["search_count"] += 1
        else:
            blocked = True

    return render_template("index.html", channels=channels, keyword=keyword,
                           growth_filter=growth_filter, genre_filter=genre_filter,
                           genres=GENRES, search_count=session["search_count"],
                           blocked=blocked, error=error)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
