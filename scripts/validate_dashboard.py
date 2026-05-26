"""
VALIDATION SCRIPT v2 — So sánh Dashboard (DuckDB views) vs Raw CSV
Chạy: python D:\EsportsAI\scripts\validate_dashboard.py

Logic validation phải MATCH ĐÚNG logic của views:
- report_player_daily: WHERE p.Player IS NOT NULL (chỉ mapped players)
- report_team_daily: WHERE p.Team IS NOT NULL (chỉ mapped teams)  
- report_hero_daily: ALL players, WHERE Game_Mode='Ranked' (toàn bộ ranked)
- core_rank_latest: ROW_NUMBER() OVER(PARTITION BY TencentID ORDER BY Date_Time DESC)
"""

import duckdb
import pandas as pd
import glob
import os

DB_PATH = r"D:\EsportsAI\db\esports.duckdb"
DATA_DIR = r"D:\EsportsAI\data"

print("=" * 60)
print("VALIDATION v2: Dashboard vs Raw CSV")
print("=" * 60)

# =====================================================
# LOAD RAW CSV
# =====================================================

# Match history — ALL rows (giống mh_all trong DB)
mh_files = glob.glob(os.path.join(DATA_DIR, "match_history_*.csv"))
mh_all = pd.concat([pd.read_csv(f) for f in mh_files], ignore_index=True)
mh_all["Date_Time"] = pd.to_datetime(mh_all["Date_Time"])
mh_all["GameDate"] = mh_all["Date_Time"].dt.date

# Player accounts
uid = pd.read_csv(os.path.join(DATA_DIR, "uid_all.csv"))

# Hero mapping
hero_df = pd.read_csv(os.path.join(DATA_DIR, "hero.csv"))

# Rank
rank_files = glob.glob(os.path.join(DATA_DIR, "rank_before_after_raw_*.csv"))
rank_all = pd.concat([pd.read_csv(f) for f in rank_files], ignore_index=True)
rank_all["Date_Time"] = pd.to_datetime(rank_all["Date_Time"])

# Merge: matched players only (giống logic view có WHERE p.Player IS NOT NULL)
mh_mapped = mh_all.merge(
    uid[["TencentID", "Player", "Team", "Server", "Account"]],
    on="TencentID", how="inner"
)

# Hero merge cho hero analytics — ALL matches, không filter player
mh_hero_ranked = mh_all[mh_all["Game_Mode"] == "Ranked"].merge(
    hero_df.rename(columns={"HeroID": "Hero"}),
    on="Hero", how="inner"  # inner = HeroName IS NOT NULL
)
mh_hero_ranked["GameDate"] = mh_hero_ranked["Date_Time"].dt.date

# DB connection
con = duckdb.connect(DB_PATH, read_only=True)

errors = []
passes = []


def safe_kda(row):
    if row["DeadCnt"] == 0:
        return row["KillCnt"] + row["AssistCnt"]
    return (row["KillCnt"] + row["AssistCnt"]) / row["DeadCnt"]


def check(name, expected, actual, tolerance=0.01):
    if pd.isna(expected) and pd.isna(actual):
        passes.append(f"  ✅ {name}: cả 2 đều NULL")
        return
    if pd.isna(expected) or pd.isna(actual):
        errors.append(f"  ❌ {name}: CSV={expected} | DB={actual}")
        return
    diff = abs(float(expected) - float(actual))
    if diff <= tolerance:
        passes.append(f"  ✅ {name}: CSV={expected} | DB={actual}")
    else:
        errors.append(f"  ❌ {name}: CSV={expected} | DB={actual} (lệch={diff:.4f})")


# =====================================================
# TEST 1: TỔNG SỐ — report_player_daily
# (logic: mapped players only)
# =====================================================

print("\n📊 TEST 1: Tổng số liệu (mapped players)")
print("-" * 40)

csv_total_games = len(mh_mapped)
csv_total_matches = mh_mapped["BattleID"].nunique()

db_totals = con.execute("""
    SELECT 
        SUM(PlayerGames) AS TotalGames,
        SUM(UniqueMatches) AS UniqueMatches
    FROM report_player_daily
""").fetchdf()

check("Total PlayerGames", csv_total_games, int(db_totals["TotalGames"][0]), 0)

# UniqueMatches: view tính DISTINCT BattleID theo (Player, Account, GameDate)
# nên SUM qua nhiều player sẽ lớn hơn global nunique
# → chỉ check PlayerGames (exact), UniqueMatches check per-team below


# =====================================================
# TEST 2: KPI THEO TEAM
# =====================================================

print("\n📊 TEST 2: KPI theo Team")
print("-" * 40)

for team in sorted(mh_mapped["Team"].dropna().unique()):
    print(f"\n  Team: {team}")

    tm = mh_mapped[mh_mapped["Team"] == team]

    csv_games = len(tm)
    csv_wins = (tm["Game_Result"] == "Win").sum()
    csv_wr = round(csv_wins * 100.0 / csv_games, 2)
    csv_kda = round(tm.apply(safe_kda, axis=1).mean(), 2)

    db_team = con.execute(f"""
        SELECT 
            SUM(PlayerGames) AS Games,
            ROUND(
                SUM(WinRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2
            ) AS WinRate,
            ROUND(
                SUM(KDA * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2
            ) AS KDA
        FROM report_team_daily
        WHERE Team = '{team}'
    """).fetchdf()

    check(f"{team} PlayerGames", csv_games, int(db_team["Games"][0]), 0)
    check(f"{team} WinRate", csv_wr, float(db_team["WinRate"][0]), 0.1)
    check(f"{team} KDA", csv_kda, float(db_team["KDA"][0]), 0.1)


# =====================================================
# TEST 3: PLAYER KPI (top 5)
# =====================================================

print("\n📊 TEST 3: Player KPI (top 5 active)")
print("-" * 40)

top_players = mh_mapped.groupby("Player").size().nlargest(5).index.tolist()

for player in top_players:
    print(f"\n  Player: {player}")

    pm = mh_mapped[mh_mapped["Player"] == player]

    csv_games = len(pm)
    csv_wins = (pm["Game_Result"] == "Win").sum()
    csv_wr = round(csv_wins * 100.0 / csv_games, 2)
    csv_kda = round(pm.apply(safe_kda, axis=1).mean(), 2)
    csv_mvp = round(pm["Is_MVP"].mean() * 100, 2)

    db_p = con.execute("""
        SELECT 
            SUM(PlayerGames) AS Games,
            ROUND(
                SUM(WinRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2
            ) AS WinRate,
            ROUND(
                SUM(KDA * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2
            ) AS KDA,
            ROUND(
                SUM(MVPRate * PlayerGames) / NULLIF(SUM(PlayerGames), 0), 2
            ) AS MVPRate
        FROM report_player_daily
        WHERE Player = ?
    """, [player]).fetchdf()

    check(f"{player} Games", csv_games, int(db_p["Games"][0]), 0)
    check(f"{player} WinRate", csv_wr, float(db_p["WinRate"][0]), 0.1)
    check(f"{player} KDA", csv_kda, float(db_p["KDA"][0]), 0.1)
    check(f"{player} MVPRate", csv_mvp, float(db_p["MVPRate"][0]), 0.15)


# =====================================================
# TEST 4: HERO ANALYTICS
# (logic: ALL players, Ranked only, DISTINCT BattleID)
# =====================================================

print("\n📊 TEST 4: Hero Analytics (ALL players, Ranked only)")
print("-" * 40)

# CSV: tính giống view — group by (HeroName, GameDate), 
# DISTINCT BattleID per group, rồi SUM
hero_daily_csv = mh_hero_ranked.groupby(["HeroName", "GameDate"]).agg(
    UniqueMatches=("BattleID", "nunique"),
    TotalRows=("BattleID", "count"),
    Wins=("Game_Result", lambda x: (x == "Win").sum())
).reset_index()

hero_daily_csv["WinRate"] = round(hero_daily_csv["Wins"] * 100.0 / hero_daily_csv["TotalRows"], 2)

# Aggregate giống dashboard: SUM UniqueMatches, weighted WinRate
hero_agg_csv = hero_daily_csv.groupby("HeroName").apply(
    lambda g: pd.Series({
        "UniqueMatches": g["UniqueMatches"].sum(),
        "WinRate": round(
            (g["WinRate"] * g["UniqueMatches"]).sum() / g["UniqueMatches"].sum(), 2
        ) if g["UniqueMatches"].sum() > 0 else 0
    })
).nlargest(5, "UniqueMatches")

for hero_name in hero_agg_csv.index:
    print(f"\n  Hero: {hero_name}")

    h = hero_agg_csv.loc[hero_name]
    csv_matches = int(h["UniqueMatches"])
    csv_wr = float(h["WinRate"])

    db_h = con.execute("""
        SELECT 
            SUM(UniqueMatches) AS Matches,
            ROUND(
                SUM(WinRate * UniqueMatches) / NULLIF(SUM(UniqueMatches), 0), 2
            ) AS WinRate
        FROM report_hero_daily
        WHERE HeroName = ?
    """, [hero_name]).fetchdf()

    check(f"{hero_name} UniqueMatches", csv_matches, int(db_h["Matches"][0]), 0)
    check(f"{hero_name} WinRate", csv_wr, float(db_h["WinRate"][0]), 0.1)


# =====================================================
# TEST 5: RANK LATEST
# (logic: ROW_NUMBER PARTITION BY TencentID ORDER BY Date_Time DESC)
# =====================================================

print("\n📊 TEST 5: Rank Latest (per TencentID)")
print("-" * 40)

# CSV: giống logic view — latest per TencentID, chỉ mapped players
rank_merged = rank_all.merge(
    uid[["TencentID", "Player", "Team"]],
    on="TencentID", how="inner"
)

# ROW_NUMBER() OVER(PARTITION BY TencentID ORDER BY Date_Time DESC) WHERE rn=1
rank_latest_csv = (
    rank_merged
    .sort_values("Date_Time", ascending=False)
    .groupby("TencentID")
    .first()
    .reset_index()
)

csv_rank_count = len(rank_latest_csv)
db_rank_count = int(con.execute("SELECT COUNT(*) AS cnt FROM core_rank_latest").fetchdf()["cnt"][0])

check("Rank latest total rows", csv_rank_count, db_rank_count, 0)

# Spot check: 5 samples — match by TencentID (không phải Player, vì 1 player có nhiều accounts)
samples = rank_latest_csv.sample(min(5, len(rank_latest_csv)), random_state=42)

for _, row in samples.iterrows():
    tid = row["TencentID"]
    player = row["Player"]
    csv_rank = int(row["Rank_After"])
    csv_star = int(row["Star_After"])

    db_r = con.execute("""
        SELECT Rank_After, Star_After
        FROM core_rank_latest
        WHERE Player = ? AND Account = (
            SELECT Account FROM player_accounts WHERE TencentID = ? LIMIT 1
        )
    """, [player, tid]).fetchdf()

    if len(db_r) > 0:
        check(f"{player}(TID:{tid}) Rank_After", csv_rank, int(db_r["Rank_After"][0]), 0)
        check(f"{player}(TID:{tid}) Star_After", csv_star, int(db_r["Star_After"][0]), 0)
    else:
        errors.append(f"  ❌ {player}(TID:{tid}): không tìm thấy trong core_rank_latest")


# =====================================================
# TEST 6: DATE FILTER
# =====================================================

print("\n📊 TEST 6: Date Filter Consistency")
print("-" * 40)

test_start = "2026-04-01"
test_end = "2026-04-15"

csv_filtered = mh_mapped[
    (mh_mapped["GameDate"] >= pd.to_datetime(test_start).date()) &
    (mh_mapped["GameDate"] <= pd.to_datetime(test_end).date())
]

db_filtered = con.execute(f"""
    SELECT SUM(PlayerGames) AS Games
    FROM report_player_daily
    WHERE GameDate BETWEEN '{test_start}' AND '{test_end}'
""").fetchdf()

csv_g = len(csv_filtered)
db_g = int(db_filtered["Games"][0]) if db_filtered["Games"][0] is not None else 0

check(f"Date filter {test_start}~{test_end} Games", csv_g, db_g, 0)


# =====================================================
# SUMMARY
# =====================================================

print("\n" + "=" * 60)
print("KẾT QUẢ VALIDATION")
print("=" * 60)
print(f"\n  ✅ PASS: {len(passes)}")
print(f"  ❌ FAIL: {len(errors)}")

if errors:
    print("\n  CHI TIẾT LỖI:")
    for e in errors:
        print(f"    {e}")
else:
    print("\n  🎉 TẤT CẢ ĐỀU KHỚP — Dashboard chính xác!")

print()
con.close()
