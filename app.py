
import os
from flask import Flask, request, render_template, session
from googleapiclient.discovery import build
from datetime import datetime

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

@app.route("/", methods=["GET"])
def index():
    if "search_count" not in session:
        session["search_count"] = 0

    keyword = request.args.get("keyword", "")
    growth_filter = request.args.get("growth_filter", "")
    genre_filter = request.args.get("genre_filter", "")

    channels = []
    blocked = False

    if keyword:
        if session["search_count"] < 50:
            youtube = build("youtube", "v3", developerKey=API_KEY)
            search_response = youtube.search().list(
                q=keyword,
                type="video",
                part="snippet",
                maxResults=30
            ).execute()

            seen = set()

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
                    pub = ch["snippet"].get("publishedAt", "")[:10]
                    subs = ch["statistics"].get("subscriberCount", 0)
                    views = ch["statistics"].get("viewCount", 0)
                    genre = guess_genre(title + desc)

                    channels.append({
                        "title": title,
                        "link": f"https://www.youtube.com/channel/{cid}",
                        "subs": format_subscribers(subs),
                        "views": format_views(views),
                        "published_at": pub,
                        "genre": genre
                    })

            session["search_count"] += 1
        else:
            blocked = True

    return render_template("index.html", channels=channels, keyword=keyword,
                           growth_filter=growth_filter, genre_filter=genre_filter,
                           genres=GENRES, search_count=session["search_count"], blocked=blocked)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
