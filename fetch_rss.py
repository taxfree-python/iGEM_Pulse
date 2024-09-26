import os
import re
import ssl
import urllib.request

import feedparser
import pandas as pd

# RSS フィードの URL
RSS_URL = "https://gitlab.igem.org/2024.atom"

# SSL 証明書の検証を無効にするためのコンテキストを作成
ssl_context = ssl._create_unverified_context()


# 過去に保存したデータを読み込む
def load_existing_data(file_path="rss_data.csv"):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame()  # 存在しない場合は空のデータフレームを返す


# `title` から team, branch_name, isSoftware を抽出する関数
def parse_title(title):
    software_match = re.search(r"Software Tools", title)
    is_software = bool(software_match)

    # Software Tools 部分を除外して team 名を取得
    team_match = re.search(r"2024 Competition / (?:Software Tools / )?(.+)", title)
    team = team_match.group(1) if team_match else "Unknown Team"

    # branch_name の抽出
    branch_match = re.search(r"branch (\S+)", title)
    branch_name = branch_match.group(1) if branch_match else "Unknown Branch"

    return team, branch_name, is_software


# `link` を短縮し、commit のみを取得する関数
def shorten_link(link):
    # "commit/" を含むリンクだけを処理
    if "commit/" in link:
        base_link = link.split("-/commit/")[0]
        return base_link
    return None  # commit 以外のリンクは無視


# 新しいデータを取得し、重複を排除
def fetch_rss_data(existing_data):
    try:
        response = urllib.request.urlopen(RSS_URL, context=ssl_context)
        feed = feedparser.parse(response)
    except Exception as e:
        print(f"Error fetching the feed: {e}")
        return pd.DataFrame()

    # フィードの内容を解析
    entries = []
    for entry in feed.entries:
        if not existing_data.empty and entry.id in existing_data["id"].values:
            continue  # 既に存在するエントリはスキップ

        team, branch_name, is_software = parse_title(entry.title)

        # link を短縮
        short_link = shorten_link(entry.link)
        if short_link:  # commit 以外のリンクはスキップ
            entries.append(
                {
                    "id": entry.id,
                    "team": team,
                    "branch_name": branch_name,
                    "isSoftware": is_software,
                    "link": short_link,
                    "updated": entry.updated,
                }
            )

    return pd.DataFrame(entries)


# CSV に保存（id でソート）
def save_data(data, file_path="rss_data.csv"):
    if not data.empty:
        # 既存データに新しいデータを追加
        existing_data = load_existing_data(file_path)
        updated_data = pd.concat([existing_data, data], ignore_index=True)

        # id でソート
        sorted_data = updated_data.sort_values(by="id", ascending=True)

        # ソートしたデータを CSV に保存
        sorted_data.to_csv(file_path, index=False)


# 実行
if __name__ == "__main__":
    existing_data = load_existing_data()
    new_data = fetch_rss_data(existing_data)
    save_data(new_data)
