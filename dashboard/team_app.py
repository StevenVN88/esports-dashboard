"""
TEAM DASHBOARD — Phiên bản cho Team Owner
Truy cập bằng token: ?token=xxx
Mỗi team nhận 1 link riêng, chỉ thấy data của team mình.
"""

import streamlit as st
import duckdb
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import tomllib
import os

# =====================================================
# CONFIG
# =====================================================

DB_PATH = "db/esports.duckdb"
if not os.path.exists(DB_PATH):
    DB_PATH = r"D:\EsportsAI\db\esports.duckdb"

st.set_page_config(page_title="Team Dashboard", page_icon="🎮", layout="wide", initial_sidebar_state="expanded")

# =====================================================
# TOKEN AUTH
# =====================================================

def load_tokens():
    paths = [
        ".streamlit/team_tokens.toml",
        os.path.join(os.path.dirname(__file__), "..", ".streamlit", "team_tokens.toml"),
        r"D:\EsportsAI\.streamlit\team_tokens.toml",
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, "rb") as f:
                data = tomllib.load(f)
            return data.get("tokens", {})
    return {}

TOKEN_MAP = load_tokens()
query_params = st.query_params
token_param = query_params.get("token", None)

if not token_param or token_param not in TOKEN_MAP:
    st.markdown("""
    <div style="text-align:center; margin-top:100px;">
        <h1 style="color:#e17055;">⚠️ Truy cập bị từ chối</h1>
        <p style="color:#888; font-size:18px;">Token không hợp lệ hoặc thiếu.<br>Liên hệ quản lý để nhận link truy cập.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

selected_team = TOKEN_MAP[token_param]

st.markdown("""
<style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Be Vietnam Pro', sans-serif; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%); }
    [data-testid="stSidebar"] .stMarkdown h1, [data-testid="stSidebar"] .stMarkdown h2, [data-testid="stSidebar"] .stMarkdown h3 { color: #e0e0ff; }
    .kpi-card { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 12px; padding: 20px 24px; border-left: 4px solid; margin-bottom: 8px; }
    .kpi-card .kpi-label { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.2px; color: #8888aa; margin-bottom: 4px; }
    .kpi-card .kpi-value { font-size: 28px; font-weight: 800; color: #e0e0ff; line-height: 1.1; }
    .kpi-card .kpi-sub { font-size: 11px; color: #6a6a8a; margin-top: 4px; }
    .section-header { font-size: 16px; font-weight: 700; color: #c0c0e0; letter-spacing: 0.5px; padding-bottom: 8px; border-bottom: 2px solid #2a2a4a; margin: 24px 0 16px 0; }
    .stTabs [data-baseweb="tab-list"] { gap: 0px; background: #0f0f1a; border-radius: 8px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { border-radius: 6px; padding: 8px 20px; font-weight: 600; font-size: 13px; }
    .stDataFrame { border-radius: 8px; overflow: hidden; }
    .stPlotlyChart { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

PLOTLY_BASE = dict(template="plotly_dark", paper_bgcolor="rgba(15,15,26,0.0)", plot_bgcolor="rgba(15,15,26,0.4)", font=dict(family="Be Vietnam Pro, sans-serif", color="#c0c0e0"), margin=dict(l=40, r=20, t=40, b=40), legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)), hoverlabel=dict(bgcolor="#1a1a2e", font_size=12, font_family="Be Vietnam Pro"))
AXIS_STYLE = dict(gridcolor="rgba(100,100,160,0.15)", zeroline=False)

def plotly_layout(**kwargs):
    layout = {**PLOTLY_BASE}
    if "xaxis" not in kwargs: kwargs["xaxis"] = AXIS_STYLE
    if "yaxis" not in kwargs: kwargs["yaxis"] = AXIS_STYLE
    layout.update(kwargs)
    return layout

COLORS = {"primary": "#6c5ce7", "success": "#00cec9", "warning": "#fdcb6e", "danger": "#e17055", "info": "#74b9ff", "accent": "#a29bfe", "gradient": ["#6c5ce7", "#a29bfe", "#74b9ff", "#00cec9", "#55efc4"]}

def kpi_card(label, value, sub="", color="#6c5ce7"):
    return f'<div class="kpi-card" style="border-left-color: {color};"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div></div>'

def section_header(text):
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)

def build_server_filter(selected_server, col_name="Server"):
    if selected_server == "ALL": return ""
    return f"AND {col_name} = '{selected_server}'"

def safe_val(df, col, idx=0, default=0):
    try:
        v = df[col].iloc[idx]
        return default if v is None else v
    except (IndexError, KeyError):
        return default

@st.cache_resource
def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)

con = get_connection()

@st.cache_data
def load_hero_icons():
    _con = get_connection()
    df = _con.execute("SELECT HeroName, Image FROM hero WHERE HeroName IS NOT NULL AND Image IS NOT NULL").fetchdf()
    return dict(zip(df["HeroName"], df["Image"]))

hero_icon_map = load_hero_icons()

# SIDEBAR
with st.sidebar:
    st.markdown(f"## 🎮 {selected_team}")
    st.markdown("---")
    selected_server = st.selectbox("🌐 Server", ["ALL", "VN", "TH", "TW"])
    st.markdown("---")
    st.markdown("##### 📅 Khoảng thời gian")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("Từ ngày", value=datetime.now() - timedelta(days=30))
    with col_d2:
        end_date = st.date_input("Đến ngày", value=datetime.now())
    st.markdown("---")
    st.markdown("<div style='text-align:center; color:#555; font-size:11px;'>Timezone: Asia/Ho_Chi_Minh<br>Team Dashboard</div>", unsafe_allow_html=True)

srv_filter = build_server_filter(selected_server)
date_between = f"BETWEEN '{start_date}' AND '{end_date}'"

tab_overview, tab_players, tab_heroes, tab_history, tab_compare, tab_profile, tab_behavior, tab_rank = st.tabs([
    "📊 Tổng Quan", "👤 Tuyển Thủ", "⚔️ Tướng", "📜 Lịch Sử Trận", "🔀 So Sánh", "🗒️ Hồ Sơ", "⚠️ Hành Vi", "🏅 Rank"
])

# =====================================================
# OVERVIEW TAB
# =====================================================

with tab_overview:
    df_team = con.execute(f"""
        SELECT SUM(PlayerGames) AS TotalGames, SUM(UniqueMatches) AS UniqueMatches,
            ROUND(SUM(WinRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS WinRate,
            ROUND(SUM(KDA * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS KDA
        FROM report_team_daily WHERE Team = '{selected_team}' AND GameDate {date_between}
    """).fetchdf()

    c1, c2, c3, c4 = st.columns(4)
    total_games = int(safe_val(df_team, "TotalGames"))
    unique_matches = int(safe_val(df_team, "UniqueMatches"))
    wr = safe_val(df_team, "WinRate")
    kda = safe_val(df_team, "KDA")

    with c1: st.markdown(kpi_card("Lượt Chơi", f"{total_games:,}", "COUNT(*)", COLORS["primary"]), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Trận Riêng Biệt", f"{unique_matches:,}", "COUNT(DISTINCT BattleID)", COLORS["info"]), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Tỉ Lệ Thắng", f"{wr}%", "Win / TotalGames", COLORS["success"] if wr >= 50 else COLORS["danger"]), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("KDA", f"{kda}", "(K+A)/D", COLORS["warning"] if kda >= 3 else COLORS["danger"]), unsafe_allow_html=True)

    section_header("📈 Biểu Đồ Tập Luyện Theo Ngày")
    df_timeline = con.execute(f"""
        SELECT GameDate, SUM(PlayerGames) AS Games, ROUND(SUM(WinRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS WinRate
        FROM report_team_daily WHERE Team = '{selected_team}' AND GameDate {date_between}
        GROUP BY GameDate ORDER BY GameDate
    """).fetchdf()

    if len(df_timeline) > 0:
        fig_tl = go.Figure()
        fig_tl.add_trace(go.Bar(x=df_timeline["GameDate"], y=df_timeline["Games"], name="Lượt chơi", marker_color=COLORS["primary"], opacity=0.7))
        fig_tl.add_trace(go.Scatter(x=df_timeline["GameDate"], y=df_timeline["WinRate"], name="WinRate %", mode="lines+markers", line=dict(color=COLORS["success"], width=2), marker=dict(size=5), yaxis="y2"))
        fig_tl.update_layout(**plotly_layout(height=360, yaxis=dict(title="Lượt chơi", gridcolor="rgba(100,100,160,0.15)", zeroline=False), yaxis2=dict(title="WinRate %", overlaying="y", side="right", showgrid=False, range=[0, 100]), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"), barmode="overlay"))
        st.plotly_chart(fig_tl, use_container_width=True)
    else:
        st.info("Không có dữ liệu trong khoảng thời gian này.")

    section_header("🏆 Top Tuyển Thủ")
    col_top1, col_top2 = st.columns(2)
    df_top = con.execute(f"""
        SELECT Player, SUM(PlayerGames) AS TotalGames,
            ROUND(SUM(WinRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS WinRate,
            ROUND(SUM(KDA * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS KDA,
            ROUND(SUM(MVPRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS MVPRate
        FROM report_player_daily WHERE Team = '{selected_team}' {srv_filter} AND GameDate {date_between}
        GROUP BY Player ORDER BY TotalGames DESC
    """).fetchdf()

    if len(df_top) > 0:
        with col_top1:
            fig = px.bar(df_top.head(10), x="TotalGames", y="Player", orientation="h", color="WinRate", color_continuous_scale=["#e17055", "#fdcb6e", "#00cec9"], labels={"TotalGames": "Lượt chơi", "Player": ""}, title="Khối Lượng Tập (Top 10)")
            fig.update_layout(**plotly_layout(height=380, coloraxis_showscale=False)); fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        with col_top2:
            fig2 = px.bar(df_top.sort_values("KDA", ascending=False).head(10), x="KDA", y="Player", orientation="h", color="MVPRate", color_continuous_scale=["#6c5ce7", "#a29bfe", "#fdcb6e"], labels={"KDA": "KDA", "Player": ""}, title="KDA (Top 10)")
            fig2.update_layout(**plotly_layout(height=380, coloraxis_showscale=False)); fig2.update_yaxes(autorange="reversed")
            st.plotly_chart(fig2, use_container_width=True)

    section_header("🏅 Phân Bố Rank")
    df_rank_dist = con.execute(f"SELECT RankName, COUNT(*) AS PlayerCount FROM core_rank_latest WHERE Team = '{selected_team}' {srv_filter} GROUP BY RankName ORDER BY RankName").fetchdf()
    if len(df_rank_dist) > 0:
        fig_r = px.bar(df_rank_dist, x="RankName", y="PlayerCount", color="PlayerCount", color_continuous_scale=[COLORS["primary"], COLORS["accent"], COLORS["success"]], labels={"RankName": "Rank", "PlayerCount": "Số tuyển thủ"})
        fig_r.update_layout(**plotly_layout(height=320, coloraxis_showscale=False)); fig_r.update_xaxes(tickangle=45)
        st.plotly_chart(fig_r, use_container_width=True)

# =====================================================
# PLAYERS TAB (with AvgDamage/Gold/Farm)
# =====================================================

with tab_players:
    section_header("📋 Bảng Tổng Hợp Tuyển Thủ")
    df_all_players = con.execute(f"""
        SELECT Player AS "Tuyển thủ", Server, Account AS "Tài khoản",
            SUM(PlayerGames) AS "Lượt chơi", SUM(RankedGames) AS "Ranked",
            ROUND(SUM(WinRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS "WR%",
            ROUND(SUM(KDA * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS "KDA",
            ROUND(SUM(MVPRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS "MVP%",
            ROUND(SUM(AvgDamage * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 0) AS "Damage TB",
            ROUND(SUM(AvgGold * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 0) AS "Gold TB",
            ROUND(SUM(AvgFarm * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 0) AS "Farm TB"
        FROM report_player_daily WHERE Team = '{selected_team}' {srv_filter} AND GameDate {date_between}
        GROUP BY Player, Server, Account ORDER BY "Lượt chơi" DESC
    """).fetchdf()

    st.dataframe(df_all_players, use_container_width=True, hide_index=True, column_config={
        "Lượt chơi": st.column_config.NumberColumn("Lượt chơi", format="%d"),
        "Ranked": st.column_config.NumberColumn("Ranked", format="%d"),
        "WR%": st.column_config.ProgressColumn("WR%", min_value=0, max_value=100, format="%.1f%%"),
        "KDA": st.column_config.NumberColumn("KDA", format="%.2f"),
        "MVP%": st.column_config.ProgressColumn("MVP%", min_value=0, max_value=100, format="%.1f%%"),
        "Damage TB": st.column_config.NumberColumn("Damage TB", format="%d"),
        "Gold TB": st.column_config.NumberColumn("Gold TB", format="%d"),
        "Farm TB": st.column_config.NumberColumn("Farm TB", format="%d"),
    })

    st.markdown("---")
    section_header("🔍 Chi Tiết Tuyển Thủ")
    players_list = con.execute(f"SELECT DISTINCT Player FROM player_accounts WHERE Team = '{selected_team}' AND Player IS NOT NULL ORDER BY Player").fetchdf()["Player"].tolist()
    selected_player = st.selectbox("Chọn tuyển thủ", players_list)

    if selected_player:
        df_p_hist = con.execute(f"""
            SELECT GameDate, SUM(PlayerGames) AS Games,
                ROUND(SUM(WinRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS WinRate,
                ROUND(SUM(KDA * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS KDA,
                ROUND(SUM(MVPRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS MVPRate,
                ROUND(SUM(AvgDamage * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 0) AS AvgDamage,
                ROUND(SUM(AvgGold * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 0) AS AvgGold,
                ROUND(SUM(AvgFarm * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 0) AS AvgFarm
            FROM report_player_daily WHERE Player = '{selected_player}' {srv_filter} AND GameDate {date_between}
            GROUP BY GameDate ORDER BY GameDate
        """).fetchdf()

        if len(df_p_hist) > 0:
            p_total = int(df_p_hist["Games"].sum()); p_w = df_p_hist["Games"].sum()
            p_wr = round((df_p_hist["WinRate"] * df_p_hist["Games"]).sum() / max(p_w, 1), 2)
            p_kda = round((df_p_hist["KDA"] * df_p_hist["Games"]).sum() / max(p_w, 1), 2)
            p_mvp = round((df_p_hist["MVPRate"] * df_p_hist["Games"]).sum() / max(p_w, 1), 2)
            p_dmg = round((df_p_hist["AvgDamage"] * df_p_hist["Games"]).sum() / max(p_w, 1), 0)
            p_gold = round((df_p_hist["AvgGold"] * df_p_hist["Games"]).sum() / max(p_w, 1), 0)
            p_farm = round((df_p_hist["AvgFarm"] * df_p_hist["Games"]).sum() / max(p_w, 1), 0)
            p_days = len(df_p_hist)

            kc1, kc2, kc3, kc4, kc5 = st.columns(5)
            with kc1: st.markdown(kpi_card("Tổng Lượt", f"{p_total}", f"{p_days} ngày tập", COLORS["primary"]), unsafe_allow_html=True)
            with kc2: st.markdown(kpi_card("WinRate", f"{p_wr}%", "", COLORS["success"]), unsafe_allow_html=True)
            with kc3: st.markdown(kpi_card("KDA", f"{p_kda}", "", COLORS["warning"]), unsafe_allow_html=True)
            with kc4: st.markdown(kpi_card("MVP", f"{p_mvp}%", "", COLORS["accent"]), unsafe_allow_html=True)
            with kc5: st.markdown(kpi_card("TB/Ngày", f"{round(p_total / max(p_days, 1), 1)}", "", COLORS["info"]), unsafe_allow_html=True)

            kd1, kd2, kd3 = st.columns(3)
            with kd1: st.markdown(kpi_card("Damage TB", f"{int(p_dmg):,}", "AVG(Total_Damage)", COLORS["danger"]), unsafe_allow_html=True)
            with kd2: st.markdown(kpi_card("Gold TB", f"{int(p_gold):,}", "AVG(Total_Gold)", COLORS["warning"]), unsafe_allow_html=True)
            with kd3: st.markdown(kpi_card("Farm TB", f"{int(p_farm):,}", "AVG(Total_Minions)", COLORS["success"]), unsafe_allow_html=True)

            fig_player = go.Figure()
            fig_player.add_trace(go.Bar(x=df_p_hist["GameDate"], y=df_p_hist["Games"], name="Lượt chơi", marker_color=COLORS["primary"], opacity=0.65))
            fig_player.add_trace(go.Scatter(x=df_p_hist["GameDate"], y=df_p_hist["WinRate"], name="WinRate %", mode="lines+markers", line=dict(color=COLORS["success"], width=2), marker=dict(size=4), yaxis="y2"))
            fig_player.add_trace(go.Scatter(x=df_p_hist["GameDate"], y=df_p_hist["KDA"], name="KDA", mode="lines+markers", line=dict(color=COLORS["warning"], width=2, dash="dot"), marker=dict(size=4), yaxis="y3"))
            fig_player.update_layout(**plotly_layout(height=380, title=f"Lịch Sử — {selected_player}", yaxis=dict(title="Lượt chơi", gridcolor="rgba(100,100,160,0.15)", zeroline=False), yaxis2=dict(title="WinRate %", overlaying="y", side="right", showgrid=False, range=[0, 100]), yaxis3=dict(overlaying="y", side="right", showgrid=False, visible=False), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)")))
            st.plotly_chart(fig_player, use_container_width=True)

            section_header("💥 Damage / Gold / Farm Theo Ngày")
            fig_ext = go.Figure()
            fig_ext.add_trace(go.Scatter(x=df_p_hist["GameDate"], y=df_p_hist["AvgDamage"], name="Damage TB", mode="lines+markers", line=dict(color=COLORS["danger"], width=2), marker=dict(size=4)))
            fig_ext.add_trace(go.Scatter(x=df_p_hist["GameDate"], y=df_p_hist["AvgGold"], name="Gold TB", mode="lines+markers", line=dict(color=COLORS["warning"], width=2), marker=dict(size=4)))
            fig_ext.add_trace(go.Scatter(x=df_p_hist["GameDate"], y=df_p_hist["AvgFarm"], name="Farm TB", mode="lines+markers", line=dict(color=COLORS["success"], width=2), marker=dict(size=4), yaxis="y2"))
            fig_ext.update_layout(**plotly_layout(height=320, yaxis=dict(title="Damage / Gold", gridcolor="rgba(100,100,160,0.15)", zeroline=False), yaxis2=dict(title="Farm", overlaying="y", side="right", showgrid=False), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)")))
            st.plotly_chart(fig_ext, use_container_width=True)
        else:
            st.info("Không có dữ liệu trong khoảng thời gian này.")

        df_p_rank = con.execute(f"SELECT Account AS \"Tài khoản\", RankName AS \"Rank\", Star_After AS \"Sao\", LastRankUpdate AS \"Cập nhật\" FROM core_rank_latest WHERE Player = '{selected_player}' ORDER BY Rank_After DESC, Star_After DESC").fetchdf()
        if len(df_p_rank) > 0:
            section_header("🏅 Rank Hiện Tại")
            st.dataframe(df_p_rank, use_container_width=True, hide_index=True)

# =====================================================
# HEROES TAB (with AvgDamage/Gold)
# =====================================================

with tab_heroes:
    st.caption("⚠️ Hero analytics — dữ liệu của team, tất cả mode")
    st.caption("📊 Lượt chơi = COUNT(*) — player workload")

    section_header("📋 Bảng Tổng Hợp Tướng")
    df_hero_all = con.execute(f"""
        SELECT HeroName AS "Tướng", SUM(PlayerGames) AS "Lượt chơi",
            ROUND(SUM(WinRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS "WR%",
            ROUND(SUM(KDA * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS "KDA",
            ROUND(SUM(MVPRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS "MVP%"
        FROM report_player_hero
        WHERE Team = '{selected_team}' {srv_filter} AND GameDate {date_between}
        GROUP BY HeroName HAVING SUM(PlayerGames) > 0 ORDER BY "Lượt chơi" DESC
    """).fetchdf()
    df_hero_all.insert(0, "Avatar", df_hero_all["Tướng"].map(hero_icon_map))

    if len(df_hero_all) > 0:
        hk1, hk2, hk3 = st.columns(3)
        with hk1: st.markdown(kpi_card("Tướng Được Chơi", f"{len(df_hero_all)}", "", COLORS["primary"]), unsafe_allow_html=True)
        with hk2: st.markdown(kpi_card("Tổng Lượt Chơi", f"{int(df_hero_all['Lượt chơi'].sum()):,}", "", COLORS["info"]), unsafe_allow_html=True)
        with hk3: st.markdown(kpi_card("Tướng Hot Nhất", df_hero_all["Tướng"].iloc[0], f"{int(df_hero_all['Lượt chơi'].iloc[0])} lượt", COLORS["success"]), unsafe_allow_html=True)

        col_h1, col_h2 = st.columns(2)
        with col_h1:
            fig_pick = px.bar(df_hero_all.head(15), x="Lượt chơi", y="Tướng", orientation="h", color="WR%", color_continuous_scale=["#e17055", "#fdcb6e", "#00cec9"], title="Top 15 — Pick Rate", labels={"Lượt chơi": "Lượt chơi", "Tướng": ""})
            fig_pick.update_layout(**plotly_layout(height=480, coloraxis_showscale=False)); fig_pick.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_pick, use_container_width=True)
        with col_h2:
            df_wr_f = df_hero_all[df_hero_all["Lượt chơi"] >= 5].sort_values("WR%", ascending=False).head(15)
            fig_wr = px.bar(df_wr_f, x="WR%", y="Tướng", orientation="h", color="MVP%", color_continuous_scale=["#6c5ce7", "#a29bfe", "#fdcb6e"], title="Top 15 — Win Rate (≥5 lượt)", labels={"WR%": "WinRate %", "Tướng": ""})
            fig_wr.update_layout(**plotly_layout(height=480, coloraxis_showscale=False)); fig_wr.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_wr, use_container_width=True)

        st.dataframe(df_hero_all, use_container_width=True, hide_index=True, column_config={
            "Avatar": st.column_config.ImageColumn("Avatar", width="small"),
            "Lượt chơi": st.column_config.NumberColumn("Lượt chơi", format="%d"),
            "WR%": st.column_config.ProgressColumn("WR%", min_value=0, max_value=100, format="%.1f%%"),
            "KDA": st.column_config.NumberColumn("KDA", format="%.2f"),
            "MVP%": st.column_config.ProgressColumn("MVP%", min_value=0, max_value=100, format="%.1f%%"),
        })

    st.markdown("---")
    section_header("🔍 Chi Tiết Tướng")
    heroes_list = con.execute(f"""
        SELECT DISTINCT HeroName FROM report_player_hero
        WHERE Team = '{selected_team}' AND GameDate {date_between} AND HeroName IS NOT NULL
        ORDER BY HeroName
    """).fetchdf()["HeroName"].tolist()
    selected_hero = st.selectbox("Chọn tướng", heroes_list)

    if selected_hero:
        hero_img = hero_icon_map.get(selected_hero)
        if hero_img:
            hi, hinfo = st.columns([1, 5])
            with hi: st.image(hero_img, width=80)
            with hinfo: st.markdown(f"### {selected_hero}")

        df_hk = con.execute(f"""
            SELECT SUM(PlayerGames) AS Matches,
                ROUND(SUM(WinRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS WinRate,
                ROUND(SUM(KDA * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS KDA,
                ROUND(SUM(MVPRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS MVPRate
            FROM report_player_hero
            WHERE Team = '{selected_team}' {srv_filter}
              AND HeroName = '{selected_hero}' AND GameDate {date_between}
        """).fetchdf()

        hm=int(safe_val(df_hk,"Matches")); hw=safe_val(df_hk,"WinRate")
        h_kda=safe_val(df_hk,"KDA"); hmvp=safe_val(df_hk,"MVPRate")
        hd1, hd2, hd3, hd4 = st.columns(4)
        with hd1: st.markdown(kpi_card("Lượt Chơi", f"{hm}", "", COLORS["primary"]), unsafe_allow_html=True)
        with hd2: st.markdown(kpi_card("WinRate", f"{hw}%", "", COLORS["success"] if hw >= 50 else COLORS["danger"]), unsafe_allow_html=True)
        with hd3: st.markdown(kpi_card("KDA", f"{h_kda}", "", COLORS["warning"]), unsafe_allow_html=True)
        with hd4: st.markdown(kpi_card("MVP Rate", f"{hmvp}%", "", COLORS["accent"]), unsafe_allow_html=True)

        df_ht = con.execute(f"""
            SELECT GameDate, SUM(PlayerGames) AS Matches,
                ROUND(SUM(WinRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS WinRate
            FROM report_player_hero
            WHERE Team = '{selected_team}' {srv_filter}
              AND HeroName = '{selected_hero}' AND GameDate {date_between}
            GROUP BY GameDate ORDER BY GameDate
        """).fetchdf()
        if len(df_ht) > 0:
            fig_ht = go.Figure()
            fig_ht.add_trace(go.Bar(x=df_ht["GameDate"], y=df_ht["Matches"], name="Lượt chơi", marker_color=COLORS["primary"], opacity=0.6))
            fig_ht.add_trace(go.Scatter(x=df_ht["GameDate"], y=df_ht["WinRate"], name="WinRate %", mode="lines+markers", line=dict(color=COLORS["success"], width=2), yaxis="y2"))
            fig_ht.update_layout(**plotly_layout(height=350, title=f"Xu Hướng — {selected_hero}", yaxis=dict(title="Lượt chơi", gridcolor="rgba(100,100,160,0.15)", zeroline=False), yaxis2=dict(title="WinRate %", overlaying="y", side="right", showgrid=False, range=[0, 100]), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)")))
            st.plotly_chart(fig_ht, use_container_width=True)

# =====================================================
# MATCH HISTORY TAB
# =====================================================

with tab_history:
    section_header("📜 Lịch Sử Trận Đấu")
    st.caption("Dữ liệu row-level từ report_match_history — chỉ hiển thị, không aggregate")

    mh_col1, mh_col2, mh_col3 = st.columns(3)
    with mh_col1:
        mh_players = con.execute(f"SELECT DISTINCT Player FROM player_accounts WHERE Team = '{selected_team}' AND Player IS NOT NULL ORDER BY Player").fetchdf()["Player"].tolist()
        mh_selected_player = st.selectbox("Tuyển thủ", ["Tất cả"] + mh_players, key="mh_player")
    with mh_col2:
        mh_mode = st.selectbox("Game Mode", ["Tất cả", "Ranked", "Normal"], key="mh_mode")
    with mh_col3:
        mh_heroes = con.execute("SELECT DISTINCT HeroName FROM hero WHERE HeroName IS NOT NULL ORDER BY HeroName").fetchdf()["HeroName"].tolist()
        mh_selected_hero = st.selectbox("Tướng", ["Tất cả"] + mh_heroes, key="mh_hero")

    mh_where = f"WHERE Team = '{selected_team}' AND Date_Time::DATE {date_between}"
    if mh_selected_player != "Tất cả": mh_where += f" AND Player = '{mh_selected_player}'"
    if selected_server != "ALL": mh_where += f" AND Server = '{selected_server}'"
    if mh_mode != "Tất cả": mh_where += f" AND Game_Mode = '{mh_mode}'"
    if mh_selected_hero != "Tất cả": mh_where += f" AND HeroName = '{mh_selected_hero}'"

    df_mh = con.execute(f"""
        SELECT Player AS "Tuyển thủ", Date_Time AS "Thời gian", HeroName AS "Tướng",
            Game_Mode AS "Mode", Game_Result AS "Kết quả", Team_Side AS "Phe",
            MatchMinutes AS "Phút", KillCnt AS "Kill", DeadCnt AS "Death", AssistCnt AS "Assist",
            Total_Damage AS "Damage", Total_Gold AS "Gold", Total_Minions AS "Farm",
            DestoryTowerCnt AS "Trụ", Hero_Level AS "Level", Is_MVP AS "MVP"
        FROM report_match_history {mh_where} ORDER BY Date_Time DESC LIMIT 500
    """).fetchdf()

    if len(df_mh) > 0:
        df_mh.insert(2, "Avatar", df_mh["Tướng"].map(hero_icon_map))
        mh_total = len(df_mh); mh_wins = int((df_mh["Kết quả"].str.contains("Win")).sum())
        mh_wr_display = round(mh_wins * 100.0 / mh_total, 1) if mh_total > 0 else 0
        # Emoji for Win/Loss visual
        df_mh["Kết quả"] = df_mh["Kết quả"].apply(lambda x: "🟢 Win" if x == "Win" else "🔴 Loss")

        mk1, mk2, mk3 = st.columns(3)
        with mk1: st.markdown(kpi_card("Hiển thị", f"{mh_total}", "rows (max 500)", COLORS["primary"]), unsafe_allow_html=True)
        with mk2: st.markdown(kpi_card("Thắng", f"{mh_wins}", f"trong {mh_total} trận", COLORS["success"]), unsafe_allow_html=True)
        with mk3: st.markdown(kpi_card("WR hiển thị", f"{mh_wr_display}%", "chỉ dữ liệu đang xem", COLORS["info"]), unsafe_allow_html=True)

        st.dataframe(df_mh, use_container_width=True, hide_index=True, height=600, column_config={
            "Avatar": st.column_config.ImageColumn("Avatar", width="small"),
            "Phút": st.column_config.NumberColumn("Phút", format="%.1f"),
            "Damage": st.column_config.NumberColumn("Damage", format="%d"),
            "Gold": st.column_config.NumberColumn("Gold", format="%d"),
            "MVP": st.column_config.CheckboxColumn("MVP"),
        })
    else:
        st.info("Không có dữ liệu lịch sử trận trong khoảng thời gian và bộ lọc này.")

# =====================================================
# PLAYER COMPARISON TAB (Radar Chart)
# =====================================================

with tab_compare:
    section_header("🔀 So Sánh Tuyển Thủ")
    st.caption("Radar chart so sánh — dữ liệu từ report_player_daily")

    cmp_players_list = con.execute(f"SELECT DISTINCT Player FROM player_accounts WHERE Team = '{selected_team}' AND Player IS NOT NULL ORDER BY Player").fetchdf()["Player"].tolist()
    cmp_selected = st.multiselect("Chọn 2-5 tuyển thủ", cmp_players_list, default=cmp_players_list[:2] if len(cmp_players_list) >= 2 else cmp_players_list, max_selections=5, key="cmp_players")

    if len(cmp_selected) >= 2:
        players_in = ", ".join([f"'{p}'" for p in cmp_selected])
        df_cmp = con.execute(f"""
            SELECT Player, SUM(PlayerGames) AS TotalGames,
                ROUND(SUM(WinRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS WinRate,
                ROUND(SUM(KDA * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS KDA,
                ROUND(SUM(MVPRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS MVPRate,
                ROUND(SUM(AvgDamage * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 0) AS AvgDamage,
                ROUND(SUM(AvgGold * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 0) AS AvgGold,
                ROUND(SUM(AvgFarm * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 0) AS AvgFarm
            FROM report_player_daily WHERE Team = '{selected_team}' {srv_filter} AND GameDate {date_between} AND Player IN ({players_in})
            GROUP BY Player
        """).fetchdf()

        if len(df_cmp) >= 2:
            metrics = ["WinRate", "KDA", "MVPRate", "AvgDamage", "AvgGold", "AvgFarm"]
            labels = ["WinRate %", "KDA", "MVP %", "Damage TB", "Gold TB", "Farm TB"]
            norm_data = {}
            for m in metrics:
                mx = df_cmp[m].max()
                norm_data[m] = (df_cmp[m] / mx * 100) if mx > 0 else (df_cmp[m] * 0)

            radar_colors = [COLORS["primary"], COLORS["success"], COLORS["danger"], COLORS["warning"], COLORS["info"]]
            fig_radar = go.Figure()
            for i, row in df_cmp.iterrows():
                vals = [float(norm_data[m].iloc[i]) for m in metrics]; vals.append(vals[0])
                color = radar_colors[i % len(radar_colors)]
                fig_radar.add_trace(go.Scatterpolar(r=vals, theta=labels + [labels[0]], fill="toself", name=row["Player"], line=dict(color=color, width=2), opacity=0.8))

            fig_radar.update_layout(
                polar=dict(bgcolor="rgba(15,15,26,0.4)", radialaxis=dict(visible=True, range=[0, 105], gridcolor="rgba(100,100,160,0.2)", tickfont=dict(size=9, color="#6a6a8a")), angularaxis=dict(gridcolor="rgba(100,100,160,0.2)", tickfont=dict(size=11, color="#c0c0e0"))),
                template="plotly_dark", paper_bgcolor="rgba(15,15,26,0.0)", font=dict(family="Be Vietnam Pro, sans-serif", color="#c0c0e0"), margin=dict(l=40, r=20, t=40, b=40), height=500, showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)", font=dict(size=12, color="#c0c0e0")), title="So Sánh Chỉ Số (normalized 0-100)")
            st.plotly_chart(fig_radar, use_container_width=True)

            section_header("📋 Bảng Số Liệu Gốc")
            df_cmp_d = df_cmp.rename(columns={"Player": "Tuyển thủ", "TotalGames": "Lượt chơi", "WinRate": "WR%", "KDA": "KDA", "MVPRate": "MVP%", "AvgDamage": "Damage TB", "AvgGold": "Gold TB", "AvgFarm": "Farm TB"})
            st.dataframe(df_cmp_d, use_container_width=True, hide_index=True, column_config={
                "WR%": st.column_config.ProgressColumn("WR%", min_value=0, max_value=100, format="%.1f%%"),
                "MVP%": st.column_config.ProgressColumn("MVP%", min_value=0, max_value=100, format="%.1f%%"),
                "Damage TB": st.column_config.NumberColumn("Damage TB", format="%d"),
                "Gold TB": st.column_config.NumberColumn("Gold TB", format="%d"),
                "Farm TB": st.column_config.NumberColumn("Farm TB", format="%d"),
            })
        else:
            st.warning("Không đủ dữ liệu cho các tuyển thủ đã chọn.")
    else:
        st.info("Chọn ít nhất 2 tuyển thủ để so sánh.")

# =====================================================
# HỒ SƠ TAB
# =====================================================

with tab_profile:
    section_header("🗒️ Hồ Sơ Tuyển Thủ")
    profile_players = con.execute(f"SELECT DISTINCT Player FROM player_accounts WHERE Team = '{selected_team}' AND Player IS NOT NULL ORDER BY Player").fetchdf()["Player"].tolist()
    profile_player = st.selectbox("Chọn tuyển thủ", profile_players, key="profile_player")

    if profile_player:
        df_pk = con.execute(f"""
            SELECT SUM(PlayerGames) AS TotalGames, SUM(RankedGames) AS RankedGames, COUNT(DISTINCT GameDate) AS ActiveDays,
                ROUND(SUM(WinRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS WinRate,
                ROUND(SUM(KDA * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS KDA,
                ROUND(SUM(MVPRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS MVPRate
            FROM report_player_daily WHERE Player = '{profile_player}' {srv_filter} AND GameDate {date_between}
        """).fetchdf()

        pf_games=int(safe_val(df_pk,"TotalGames")); pf_ranked=int(safe_val(df_pk,"RankedGames")); pf_days=int(safe_val(df_pk,"ActiveDays"))
        pf_wr=safe_val(df_pk,"WinRate"); pf_kda=safe_val(df_pk,"KDA"); pf_mvp=safe_val(df_pk,"MVPRate")

        df_ph = con.execute(f"""
            SELECT HeroName, SUM(PlayerGames) AS PlayerGames,
                ROUND(SUM(WinRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS WinRate,
                ROUND(SUM(KDA * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS KDA,
                ROUND(SUM(MVPRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS MVPRate
            FROM report_player_hero WHERE Player = '{profile_player}' {srv_filter} AND GameDate {date_between}
            GROUP BY HeroName ORDER BY PlayerGames DESC
        """).fetchdf()

        pk1, pk2, pk3, pk4, pk5, pk6 = st.columns(6)
        with pk1: st.markdown(kpi_card("Lượt Chơi", f"{pf_games:,}", f"{pf_days} ngày", COLORS["primary"]), unsafe_allow_html=True)
        with pk2: st.markdown(kpi_card("Ranked", f"{pf_ranked:,}", "", COLORS["info"]), unsafe_allow_html=True)
        with pk3: st.markdown(kpi_card("Tướng", f"{len(df_ph)}", "Hero Pool", COLORS["accent"]), unsafe_allow_html=True)
        with pk4: st.markdown(kpi_card("WR%", f"{pf_wr}%", "", COLORS["success"] if pf_wr >= 50 else COLORS["danger"]), unsafe_allow_html=True)
        with pk5: st.markdown(kpi_card("KDA", f"{pf_kda}", "", COLORS["warning"]), unsafe_allow_html=True)
        with pk6: st.markdown(kpi_card("MVP%", f"{pf_mvp}%", "", COLORS["accent"]), unsafe_allow_html=True)

        col_pool, col_tl = st.columns([2, 3])
        with col_pool:
            section_header("⚔️ Hero Pool")
            if len(df_ph) > 0:
                df_ph.insert(0, "Avatar", df_ph["HeroName"].map(hero_icon_map))
                df_ph = df_ph.rename(columns={"HeroName": "Tướng", "PlayerGames": "Trận", "WinRate": "WR%", "KDA": "KDA", "MVPRate": "MVP%"})
                st.dataframe(df_ph, use_container_width=True, hide_index=True, height=460, column_config={
                    "Avatar": st.column_config.ImageColumn("Avatar", width="small"),
                    "WR%": st.column_config.ProgressColumn("WR%", min_value=0, max_value=100, format="%.1f%%"),
                    "MVP%": st.column_config.ProgressColumn("MVP%", min_value=0, max_value=100, format="%.1f%%"),
                })

        with col_tl:
            section_header("📈 Lịch Sử")
            df_pfh = con.execute(f"""
                SELECT GameDate, SUM(PlayerGames) AS Games, SUM(RankedGames) AS Ranked,
                    ROUND(SUM(WinRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2) AS WinRate
                FROM report_player_daily WHERE Player = '{profile_player}' {srv_filter} AND GameDate {date_between}
                GROUP BY GameDate ORDER BY GameDate
            """).fetchdf()

            if len(df_pfh) > 0:
                df_pfh["GameDate"] = df_pfh["GameDate"].astype(str)
                fig_pf = go.Figure()
                fig_pf.add_trace(go.Scatter(x=df_pfh["GameDate"], y=df_pfh["Ranked"], name="Ranked", mode="lines+markers", line=dict(color=COLORS["danger"], width=2), marker=dict(size=5), fill="tozeroy", fillcolor="rgba(225,112,85,0.15)"))
                fig_pf.add_trace(go.Scatter(x=df_pfh["GameDate"], y=df_pfh["Games"] - df_pfh["Ranked"], name="Normal", mode="lines+markers", line=dict(color=COLORS["info"], width=2), marker=dict(size=4)))
                fig_pf.update_layout(**plotly_layout(height=240, title="Lượt chơi theo ngày", yaxis=dict(title="Lượt", gridcolor="rgba(100,100,160,0.15)", zeroline=False), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)")))
                st.plotly_chart(fig_pf, use_container_width=True)

                fig_wr = go.Figure()
                fig_wr.add_trace(go.Scatter(x=df_pfh["GameDate"], y=df_pfh["WinRate"], name="WinRate %", mode="lines+markers", line=dict(color=COLORS["success"], width=2), marker=dict(size=5)))
                fig_wr.add_hline(y=50, line_dash="dot", line_color="rgba(255,255,255,0.2)")
                fig_wr.update_layout(**plotly_layout(height=200, title="WinRate theo ngày", yaxis=dict(title="WR%", gridcolor="rgba(100,100,160,0.15)", zeroline=False, range=[0, 100]), showlegend=False))
                st.plotly_chart(fig_wr, use_container_width=True)
            else:
                st.info("Không có dữ liệu trong khoảng thời gian này.")

        df_pfr = con.execute(f"SELECT Account AS \"Tài khoản\", RankName AS \"Rank\", Star_After AS \"Sao\", LastRankUpdate AS \"Cập nhật\" FROM core_rank_latest WHERE Player = '{profile_player}' ORDER BY Rank_After DESC, Star_After DESC").fetchdf()
        if len(df_pfr) > 0:
            section_header("🏅 Rank Hiện Tại")
            st.dataframe(df_pfr, use_container_width=True, hide_index=True)


# =====================================================
# BEHAVIOR TAB
# =====================================================

with tab_behavior:
    section_header("⚠️ Báo Cáo Hành Vi")
    df_bh = con.execute(f"""
        SELECT SUM(TotalReports) AS Reports, SUM(AFK) AS AFK, SUM(Feeding) AS Feeding,
            SUM(Bad_Words) AS Bad_Words, SUM(Sabotage) AS Sabotage, SUM(Lane_Stealing) AS Lane_Stealing, SUM(Hack) AS Hack
        FROM report_behavior WHERE Team = '{selected_team}' {srv_filter} AND GameDate {date_between}
    """).fetchdf()

    bh_total=int(safe_val(df_bh,"Reports")); bh_afk=int(safe_val(df_bh,"AFK")); bh_feed=int(safe_val(df_bh,"Feeding"))
    bh_bad=int(safe_val(df_bh,"Bad_Words")); bh_sab=int(safe_val(df_bh,"Sabotage")); bh_lane=int(safe_val(df_bh,"Lane_Stealing")); bh_hack=int(safe_val(df_bh,"Hack"))

    bk1,bk2,bk3,bk4,bk5,bk6,bk7 = st.columns(7)
    with bk1: st.markdown(kpi_card("Tổng", f"{bh_total:,}", "", COLORS["danger"]), unsafe_allow_html=True)
    with bk2: st.markdown(kpi_card("AFK", f"{bh_afk}", "", COLORS["warning"]), unsafe_allow_html=True)
    with bk3: st.markdown(kpi_card("Feeding", f"{bh_feed}", "", COLORS["danger"]), unsafe_allow_html=True)
    with bk4: st.markdown(kpi_card("Bad Words", f"{bh_bad}", "", COLORS["accent"]), unsafe_allow_html=True)
    with bk5: st.markdown(kpi_card("Sabotage", f"{bh_sab}", "", COLORS["info"]), unsafe_allow_html=True)
    with bk6: st.markdown(kpi_card("Lane Steal", f"{bh_lane}", "", COLORS["primary"]), unsafe_allow_html=True)
    with bk7: st.markdown(kpi_card("Hack", f"{bh_hack}", "", "#ff0000" if bh_hack > 0 else COLORS["success"]), unsafe_allow_html=True)

    col_bc, col_bp = st.columns([3, 2])
    with col_bc:
        section_header("📈 Report Theo Ngày")
        df_bd = con.execute(f"""
            SELECT GameDate, SUM(AFK) AS AFK, SUM(Feeding) AS Feeding, SUM(Bad_Words) AS Bad_Words
            FROM report_behavior WHERE Team = '{selected_team}' {srv_filter} AND GameDate {date_between}
            GROUP BY GameDate ORDER BY GameDate
        """).fetchdf()
        if len(df_bd) > 0:
            df_bd["GameDate"] = df_bd["GameDate"].astype(str)
            fig_bh = go.Figure()
            fig_bh.add_trace(go.Bar(x=df_bd["GameDate"], y=df_bd["AFK"], name="AFK", marker_color=COLORS["warning"]))
            fig_bh.add_trace(go.Bar(x=df_bd["GameDate"], y=df_bd["Feeding"], name="Feeding", marker_color=COLORS["danger"]))
            fig_bh.add_trace(go.Bar(x=df_bd["GameDate"], y=df_bd["Bad_Words"], name="Bad Words", marker_color=COLORS["accent"]))
            fig_bh.update_layout(**plotly_layout(height=350, barmode="stack", yaxis=dict(title="Số report", gridcolor="rgba(100,100,160,0.15)", zeroline=False), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)")))
            st.plotly_chart(fig_bh, use_container_width=True)
    with col_bp:
        section_header("📊 Phân Bố")
        if bh_total > 0:
            cats = {k: v for k, v in {"AFK": bh_afk, "Feeding": bh_feed, "Bad Words": bh_bad, "Sabotage": bh_sab, "Lane Steal": bh_lane, "Hack": bh_hack}.items() if v > 0}
            if cats:
                fig_bp = px.pie(names=list(cats.keys()), values=list(cats.values()), hole=0.5, color_discrete_sequence=[COLORS["warning"], COLORS["danger"], COLORS["accent"], COLORS["info"], COLORS["primary"], "#ff0000"])
                fig_bp.update_layout(**plotly_layout(height=350, showlegend=True))
                fig_bp.update_traces(textinfo="label+percent", textfont_size=11)
                st.plotly_chart(fig_bp, use_container_width=True)

    section_header("👤 Chi Tiết Theo Tuyển Thủ")
    df_bp = con.execute(f"""
        SELECT Player AS "Tuyển thủ", SUM(TotalReports) AS "Tổng", SUM(AFK) AS "AFK", SUM(Feeding) AS "Feeding",
            SUM(Bad_Words) AS "Bad Words", SUM(Sabotage) AS "Sabotage", SUM(Lane_Stealing) AS "Lane Steal", SUM(Hack) AS "Hack"
        FROM report_behavior WHERE Team = '{selected_team}' {srv_filter} AND GameDate {date_between}
        GROUP BY Player ORDER BY "Tổng" DESC
    """).fetchdf()
    if len(df_bp) > 0:
        st.dataframe(df_bp, use_container_width=True, hide_index=True)
    else:
        st.info("Không có báo cáo hành vi.")


# =====================================================
# RANK TAB
# =====================================================

with tab_rank:
    section_header("🏅 Bảng Xếp Hạng Hiện Tại")
    st.caption("Rank mới nhất theo TencentID (ROW_NUMBER by Date_Time DESC)")

    df_rank = con.execute(f"""
        SELECT Player AS "Tuyển thủ", Server, Account AS "Tài khoản", RankName AS "Rank", Star_After AS "Sao", LastRankUpdate AS "Cập nhật lần cuối"
        FROM core_rank_latest WHERE Team = '{selected_team}' {srv_filter}
        ORDER BY Rank_After DESC, Star_After DESC
    """).fetchdf()

    if len(df_rank) > 0:
        df_rg = df_rank.groupby("Rank").size().reset_index(name="Count")
        col_r1, col_r2 = st.columns([1, 2])
        with col_r1:
            fig_d = px.pie(df_rg, names="Rank", values="Count", hole=0.55, color_discrete_sequence=COLORS["gradient"], title="Phân Bố Rank")
            fig_d.update_layout(**plotly_layout(height=400, showlegend=True, legend=dict(font=dict(size=10))))
            fig_d.update_traces(textposition="inside", textinfo="value", textfont_size=11)
            st.plotly_chart(fig_d, use_container_width=True)
        with col_r2:
            st.dataframe(df_rank, use_container_width=True, hide_index=True, height=400)
    else:
        st.info("Không có dữ liệu rank cho đội này.")
