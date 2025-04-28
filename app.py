from flask import Flask, render_template, request, session
from googleapiclient.discovery import build
from dateutil import parser
import datetime
import os

# 設定ファイル読み込み
import config

app = Flask(__name__)
app.secret_key = os.urandom(24)

# YouTube APIキー（環境変数から取得）
API_KEY = os.environ.get("YOUTUBE_API_KEY")

@app.route("/", methods=["GET", "POST"])
def index():
    # セッションに検索回数を保持（初回アクセス時）
    if "search_count" not in session:
        session["search_count"] = 0
        session["last_reset"] = datetime.datetime.utcnow().date()

    # 毎日リセット（0時）
    today = datetime.datetime.utcnow().date()
    if session.get("last_reset") != today:
        session["search_count"] = 0
        session["last_reset"] = today

    channels = []

    if request.method == "POST":
        if session["search_count"] >= config.MAX_SEARCH_COUNT_PER_DAY:
            return render_template("index.html", channels=[], message="1日の検索回数制限に達しました。明日までお待ちください。", search_count=session["search_count"], max_count=config.MAX_SEARCH_COUNT_PER_DAY)

        keyword = request.form.get("keyword")
        category = request.form.get("category")
        use_3m_filter = request.form.get("use_3m_filter")
        use_6m_filter = request.form.get("use_6m_filter")

        youtube = build("youtube", "v3", developerKey=API_KEY)

        # 動画検索
        search_response = youtube.search().list(
            q=keyword,
            part="snippet",
            type="video",
            maxResults=30,
            publishedAfter=(datetime.datetime.utcnow() - datetime.timedelta(days=180)).isoformat("T") + "Z"
        ).execute()

        seen_channels = set()

        for item in search_response.get("items", []):
            channel_id = item["snippet"]["channelId"]
            channel_title = item["snippet"]["channelTitle"]

            # チャンネル重複防止
            if channel_id in seen_channels:
                continue
            seen_channels.add(channel_id)

            # チャンネル情報取得
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

                # 成長フィルター適用
                is_new_channel = True
                if use_3m_filter:
                    if (datetime.datetime.utcnow() - published_at).days > config.NEW_CHANNEL_DAYS_3M:
                        is_new_channel = False
                elif use_6m_filter:
                    if (datetime.datetime.utcnow() - published_at).days > config.NEW_CHANNEL_DAYS_6M:
                        is_new_channel = False

                if is_new_channel and subs >= 1000 and views >= 10000:
                    channels.append({
                        "title": channel_title,
                        "url": f"https://www.youtube.com/channel/{channel_id}",
                        "subscribers": f"{subs:,}",
                        "views": f"{views:,}",
                        "created": published_at.strftime("%Y/%m/%d")
                    })

        session["search_count"] += 1  # 検索回数カウントアップ

    return render_template("index.html", channels=channels, message=None, search_count=session["search_count"], max_count=config.MAX_SEARCH_COUNT_PER_DAY)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
