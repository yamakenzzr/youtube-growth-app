from flask import Flask, render_template, request, session, redirect, url_for
from datetime import datetime
import os
import math

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 日本式数値表記関数
def format_number_jp(num):
    try:
        num = int(num)
    except (ValueError, TypeError):
        return "-"
    if num >= 10**8:
        return f"{round(num / 10**8, 1)}億"
    elif num >= 10**4:
        return f"{round(num / 10**4, 1)}万"
    return str(num)

# ジャンル分類辞書（23ジャンル＋未分類）
genre_dict = {
    "教育・解説": ["勉強", "解説", "学習", "知識", "講座"],
    "ビジネス・副業": ["ビジネス", "副業", "起業", "お金", "投資"],
    "ゲーム・実況": ["ゲーム", "実況", "プレイ", "配信"],
    "エンタメ・バラエティ": ["エンタメ", "バラエティ", "お笑い", "ネタ"],
    "音楽・歌ってみた": ["音楽", "歌", "演奏", "バンド", "ボカロ"],
    "美容・ファッション": ["メイク", "コスメ", "美容", "ファッション"],
    "グルメ・料理": ["料理", "レシピ", "食べ", "グルメ"],
    "Vlog・ライフスタイル": ["Vlog", "暮らし", "日常", "ライフスタイル"],
    "ママ・育児": ["育児", "子育て", "ママ", "パパ"],
    "ペット・動物": ["犬", "猫", "ペット", "動物"],
    "スポーツ・筋トレ・健康": ["筋トレ", "運動", "健康", "フィットネス"],
    "車・バイク・乗り物": ["車", "バイク", "ドライブ", "モータースポーツ"],
    "占い・スピリチュアル": ["占い", "スピリチュアル", "運勢", "オーラ"],
    "作業・DIY・クラフト": ["DIY", "クラフト", "ハンドメイド", "作業"],
    "旅行・観光": ["旅行", "観光", "旅", "ツアー"],
    "科学・テクノロジー": ["科学", "テクノロジー", "技術", "研究"],
    "ニュース・社会": ["ニュース", "社会", "時事", "事件"],
    "恋愛・人間関係": ["恋愛", "人間関係", "カップル", "夫婦"],
    "精神・メンタルヘルス": ["メンタル", "悩み", "心理", "心"],
    "漫画・アニメ・キャラ": ["漫画", "アニメ", "キャラクター"],
    "アイドル・K-POP": ["K-POP", "アイドル", "韓国"],
    "商品レビュー・開封": ["レビュー", "開封", "ガジェット", "商品"],
    "未分類": []
}

# サンプルデータ
channels_data = [
    {
        "title": "テストチャンネル",
        "subscribers": 123000,
        "views": 5600000,
        "videoCount": 120,
        "views_per_subscriber": 45,
        "genre": "エンタメ・バラエティ",
        "publishedAt": "2023-01-15",
        "thumbnail": "/static/no-image.png"
    }
]

@app.route('/')
def index():
    return render_template('index.html', channels=channels_data, format_number_jp=format_number_jp)

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
