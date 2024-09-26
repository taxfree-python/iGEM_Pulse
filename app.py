import pandas as pd
import plotly.express as px
import streamlit as st

# アプリの全体の幅を広げる設定
st.set_page_config(layout="wide")


# CSV ファイルからデータを読み込む
@st.cache_data
def load_data(file_path="rss_data.csv"):
    return pd.read_csv(file_path)


@st.cache_data
def load_teams_info(file_path="teams_info.csv"):
    return pd.read_csv(file_path)


# チームごとのコミット数を集計し、URLリンクも含める
def count_commits_by_team(data):
    team_commit_counts = data.groupby("team").size().reset_index(name="commits")
    team_links = data.groupby("team")["link"].first().reset_index(name="link")

    # コミット数でソート（降順）
    sorted_data = team_commit_counts.sort_values(
        by="commits", ascending=False
    ).reset_index(drop=True)
    sorted_links = team_links.set_index("team").loc[sorted_data["team"]].reset_index()

    return sorted_data, sorted_links


# ハイパーリンクを作成
def make_clickable(link, text):
    return f'<a href="{link}" target="_blank">{text}</a>'


# インタラクティブな横向き棒グラフを描画
def plot_commit_counts_interactive(team_commit_counts, team_links):
    # データの数に基づいて高さを動的に設定（1バーあたり40ピクセル）
    num_teams = len(team_commit_counts)
    graph_height = num_teams * 40  # 1バーあたり40ピクセルの高さを割り当て

    fig = px.bar(
        team_commit_counts,
        x="commits",
        y="team",
        orientation="h",  # 横向きの棒グラフ
        labels={"team": "Team", "commits": "Number of Commits"},
        title="Team-wise Commit Counts (Sorted)",
    )

    # hovertemplate をカスタマイズし、URLを表示しないようにする
    fig.update_traces(
        customdata=team_links["link"],
        hovertemplate="<b>%{y}</b><br>Commits: %{x}<extra></extra>",  # URL を表示しない
        marker_color="blue",
    )

    # チームごとの順序を反転して一番多いのを上に
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        height=graph_height,  # データの数に応じたグラフの高さを設定
    )

    return fig


# Streamlit アプリ
st.title("Team-wise Commit Visualization with Clickable Links")

# データを読み込む
data = load_data()
teams_info = load_teams_info()

# データが存在する場合のみ可視化を実行
if not data.empty and not teams_info.empty:
    # チームごとのコミット数とリンクをカウントし、ソート
    team_commit_counts, team_links = count_commits_by_team(data)

    # チーム情報と結合して、track、section、wiki を追加
    combined_data = pd.concat([team_commit_counts, team_links["link"]], axis=1)
    combined_data["GitLab link"] = combined_data["link"].apply(
        lambda x: make_clickable(x, "GitLab link")
    )  # リンクをハイパーリンクに変換
    combined_data.drop(columns=["link"], inplace=True)

    # teams_info.csv と結合して Wiki link を追加
    teams_info["Wiki link"] = teams_info["wiki"].apply(
        lambda x: make_clickable(x, "Wiki link")
    )
    combined_data = pd.merge(
        combined_data,
        teams_info[["team", "track", "section", "Wiki link"]],
        on="team",
        how="left",
    )

    # ランキングIDを振る
    combined_data.insert(
        0, "Rank", combined_data.index + 1
    )  # Rankを1からスタートさせる

    # グラフを作成
    fig = plot_commit_counts_interactive(team_commit_counts, team_links)
    st.plotly_chart(fig, use_container_width=True)

    # チームごとのコミット数とリンク、track、section、Wiki link を表示するテーブル
    with st.expander("Show detailed table"):
        st.write(
            combined_data.style.set_properties(**{"text-align": "left"}).to_html(
                index=False, escape=False
            ),
            unsafe_allow_html=True,
        )

else:
    st.write("No data available.")
