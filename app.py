from flask import Flask, render_template, request, session
from googleapiclient.discovery import build
import datetime
import os
import config

app = Flask(__name__)
app.secret_key = os.urandom(24)

API_KEY = os.environ.get("YOUTUBE_API_KEY")

# 登録者数・再生数を漢字付きで整形する
def format_count(n, type="人"):
    if n < 10000:
        return f"{n:,}{type}"
    else:
        return f"{n // 10000}万{type}"

@app.route("/", methods=["GET", "POST"])
def index():
    if "search_count" not in session:
        session["search_count"] = 0
        session["last_reset"] = datetime.datetime.utcnow().date()

    today = datetime.datetime.utcnow().date()
    if session.get("last_reset") != today:
        session["search_count"] = 0
        session["last_reset"] = today

    channels = []
    message = None

    if request.method == "POST":
        # 必ずカウントアップ
        session["search_count"] += 1

        if session["search_count"] > config.MAX_SEARCH_COUNT_PER_DAY:
            return render_template("index.html", channels=[], message="1日の検索回数制限に達しました。", search_count=session["search_count"], max_count=config.MAX_SEARCH_COUNT_PER_DAY)

        keyword = request.form.get("keyword", "")
        use_3m_filter = request.form.get("use_3m_filter") == "on"
        use_6m_filter = request.form.get("use_6m_filter") == "on"

        youtube = build("youtube", "v3", developerKey=API_KEY)

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

            if channel_id in seen_channels:
                continue
            seen_channels.add(channel_id)

            ch_data = youtube.channels().list(
                part="snippet,statistics",
                id=channel_id
            ).execute()

            if ch_data["items"]:
                ch = ch_data["items"][0]
                stats = ch["statistics"]
                subs = int(stats.get("subscriberCount", 0))
                views = int(stats.get("viewCount", 0))

                published_at_str = ch["snippet"].get("publishedAt")
                if not published_at_str:
                    continue

                try:
                    published_at = datetime.datetime.strptime(published_at_str, "%Y-%m-%dT%H:%M:%SZ")
                except Exception:
                    continue

                # 成長フィルター適用
                is_new_channel = True
                if use_3m_filter and (datetime.datetime.utcnow() - published_at).days > config.NEW_CHANNEL_DAYS_3M:
                    is_new_channel = False
                if use_6m_filter and (datetime.datetime.utcnow() - published_at).days > config.NEW_CHANNEL_DAYS_6M:
                    is_new_channel = False

                if is_new_channel and subs >= 1000 and views >= 10000:
                    channels.append({
                        "title": channel_title,
                        "url": f"https://www.youtube.com/channel/{channel_id}",
                        "subscribers": format_count(subs, "人"),
                        "views": format_count(views, "回再生"),
                        "created": published_at.strftime("%Y/%m/%d")
                    })

    return render_template("index.html", channels=channels, message=message, search_count=session["search_count"], max_count=config.MAX_SEARCH_COUNT_PER_DAY)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
