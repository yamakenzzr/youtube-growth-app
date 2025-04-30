
import os
from flask import Flask, request, render_template, session
from googleapiclient.discovery import build
from datetime import datetime, timezone
from dateutil.parser import parse

app = Flask(__name__)
app.secret_key = os.urandom(24)
API_KEY = os.environ.get("YOUTUBE_API_KEY")

GENRES = ["教育・解説", "ビジネス・副業", "エンタメ・バラエティ", "ゲーム・実況"]

def guess_genre(text):
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
        ratio = int(views) / int(subs)
        return f"{ratio:.2f}回/人"
    except:
        return "N/A"

@app.route("/", methods=["GET"])
def index():
    if "search_count" not in session:
        session["search_count"] = 0

    keyword = request.args.get("keyword", "")
    growth_filter = request.args.get("growth_filter", "")
    genre_filter = request.args.get("genre_filter", "")
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

                    channels.append({
                        "title": title,
                        "link": f"https://www.youtube.com/channel/{cid}",
                        "subs": format_subscribers(subs),
                        "views": format_views(views),
                        "videos": format_videos(videos),
                        "ratio": ratio,
                        "published_at": pub_dt.strftime("%Y-%m-%d"),
                        "genre": genre
                    })

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
