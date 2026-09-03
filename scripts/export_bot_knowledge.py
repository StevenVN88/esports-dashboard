"""
export_bot_knowledge.py
=======================
Export summary CSVs tu DuckDB reporting views -> D:\Projects\EsportsAI\reports\bot_knowledge\
Dung cho SeaTalk AI Bot (Alpha Knowledge) knowledge base.

Chay sau UPDATE_DATA.bat de bot luon co data moi nhat.
"""

import duckdb
import pandas as pd
import os
from datetime import datetime

# -- Paths ------------------------------------------------------------------
BASE_DIR  = r"D:\Projects\EsportsAI"
DB_PATH   = os.path.join(BASE_DIR, "db", "esports.duckdb")
OUT_DIR   = os.path.join(BASE_DIR, "reports", "bot_knowledge")
os.makedirs(OUT_DIR, exist_ok=True)

con = duckdb.connect(DB_PATH, read_only=True)
today = datetime.now().strftime("%Y-%m-%d %H:%M")

print(f"[{today}] Bat dau export bot knowledge...")

def export(name, sql):
    df = con.execute(sql).df()
    path = os.path.join(OUT_DIR, f"{name}.csv")
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  v {name}.csv  ({len(df)} rows)")
    return df


# ══════════════════════════════════════════════════════════════════════════
# 1. PLAYER SUMMARY
# ══════════════════════════════════════════════════════════════════════════
export("01_player_summary", """
SELECT
    Player, Team, Server,
    SUM(PlayerGames)                                              AS TotalGames,
    SUM(RankedGames)                                              AS RankedGames,
    ROUND(SUM(WinRate * PlayerGames) / SUM(PlayerGames), 2)      AS WinRate_pct,
    ROUND(SUM(KDA    * PlayerGames) / SUM(PlayerGames), 2)       AS KDA,
    ROUND(SUM(MVPRate* PlayerGames) / SUM(PlayerGames), 2)       AS MVPRate_pct,
    ROUND(SUM(AvgDamage * PlayerGames) / SUM(PlayerGames), 0)    AS AvgDamage,
    ROUND(SUM(AvgGold   * PlayerGames) / SUM(PlayerGames), 0)    AS AvgGold,
    ROUND(SUM(AvgFarm   * PlayerGames) / SUM(PlayerGames), 0)    AS AvgFarm
FROM report_player_daily
GROUP BY Player, Team, Server
ORDER BY Team, WinRate_pct DESC
""")


# ══════════════════════════════════════════════════════════════════════════
# 2. TEAM SUMMARY
# ══════════════════════════════════════════════════════════════════════════
export("02_team_summary", """
SELECT
    Team, Server,
    SUM(PlayerGames)                                              AS TotalPlayerGames,
    COUNT(DISTINCT GameDate)                                      AS ActiveDays,
    ROUND(SUM(WinRate * PlayerGames) / SUM(PlayerGames), 2)      AS WinRate_pct,
    ROUND(SUM(KDA    * PlayerGames) / SUM(PlayerGames), 2)       AS KDA,
    ROUND(SUM(MVPRate* PlayerGames) / SUM(PlayerGames), 2)       AS MVPRate_pct
FROM report_player_daily
GROUP BY Team, Server
ORDER BY WinRate_pct DESC
""")


# ══════════════════════════════════════════════════════════════════════════
# 3. HERO SUMMARY
# ══════════════════════════════════════════════════════════════════════════
export("03_hero_summary", """
SELECT
    HeroName                                                      AS Hero,
    COUNT(*)                                                      AS TotalPicks,
    ROUND(SUM(WinRate * UniqueMatches) / SUM(UniqueMatches), 2)  AS WinRate_pct,
    ROUND(AVG(MVPRate), 2)                                        AS MVPRate_pct,
    ROUND(AVG(AvgDamage), 0)                                      AS AvgDamage,
    ROUND(AVG(AvgGold), 0)                                        AS AvgGold
FROM report_hero_daily
GROUP BY HeroName
ORDER BY TotalPicks DESC
""")


# ══════════════════════════════════════════════════════════════════════════
# 4. RANK CURRENT
# ══════════════════════════════════════════════════════════════════════════
export("04_rank_current", """
SELECT
    r.Player, r.Team, r.Server,
    r.Rank_After  AS CurrentRank,
    r.Star_After  AS CurrentStar,
    r.Date_Time   AS LastUpdated
FROM (
    SELECT
        pa.Player, pa.Team, pa.Server,
        ra.Rank_After, ra.Star_After, ra.Date_Time,
        ROW_NUMBER() OVER (
            PARTITION BY ra.TencentID
            ORDER BY ra.Date_Time DESC
        ) AS rn
    FROM rank_all ra
    LEFT JOIN player_accounts pa ON ra.TencentID = pa.TencentID
    WHERE pa.Player IS NOT NULL
) r
WHERE r.rn = 1
ORDER BY r.Team, r.Player
""")


# ══════════════════════════════════════════════════════════════════════════
# 5. PLAYER HERO POOL
# ══════════════════════════════════════════════════════════════════════════
export("05_player_hero_pool", """
SELECT
    Player, Team,
    HeroName                                                      AS Hero,
    SUM(PlayerGames)                                              AS Games,
    ROUND(SUM(WinRate * PlayerGames) / SUM(PlayerGames), 2)      AS WinRate_pct,
    ROUND(SUM(KDA     * PlayerGames) / SUM(PlayerGames), 2)      AS KDA
FROM report_player_hero
GROUP BY Player, Team, HeroName
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY Player
    ORDER BY SUM(PlayerGames) DESC
) <= 5
ORDER BY Player, Games DESC
""")


# ══════════════════════════════════════════════════════════════════════════
# 6. TEAM DAILY LAST 30 DAYS — de bot tra loi cau hoi theo thoi gian
# ══════════════════════════════════════════════════════════════════════════
export("06_team_daily_last30", """
SELECT
    Team,
    Server,
    GameDate,
    SUM(PlayerGames)                                              AS PlayerGames,
    COUNT(DISTINCT UniqueMatches)                                 AS Matches,
    ROUND(SUM(WinRate * PlayerGames) / SUM(PlayerGames), 2)      AS WinRate_pct,
    ROUND(SUM(KDA    * PlayerGames) / SUM(PlayerGames), 2)       AS KDA
FROM report_player_daily
WHERE GameDate >= CURRENT_DATE - INTERVAL 30 DAYS
GROUP BY Team, Server, GameDate
ORDER BY Team, GameDate DESC
""")


# ══════════════════════════════════════════════════════════════════════════
# 7. PLAYER DAILY LAST 30 DAYS — form gan day cua tung player
# ══════════════════════════════════════════════════════════════════════════
export("07_player_daily_last30", """
SELECT
    Player, Team, Server,
    GameDate,
    PlayerGames,
    UniqueMatches,
    WinRate                                                       AS WinRate_pct,
    KDA,
    MVPRate                                                       AS MVPRate_pct
FROM report_player_daily
WHERE GameDate >= CURRENT_DATE - INTERVAL 30 DAYS
ORDER BY Player, GameDate DESC
""")


# ══════════════════════════════════════════════════════════════════════════
# SYSTEM INFO — cap nhat them file moi
# ══════════════════════════════════════════════════════════════════════════
info_path = os.path.join(OUT_DIR, "00_system_info.txt")
with open(info_path, "w", encoding="utf-8") as f:
    f.write(f"""ESPORTSAI BOT KNOWLEDGE BASE
=============================
Last updated : {today}
Today's date : {datetime.now().strftime("%Y-%m-%d")}
Teams        : BOX, FPT, SGP, FPL, 1S, GAM, TS, BOM, RRQ
Servers      : VN, TH, TW
Game         : Arena of Valor (AOV)

Files in this knowledge base:
  01_player_summary.csv      -- KPI tong hop toan thoi gian theo player
  02_team_summary.csv        -- KPI toan thoi gian theo team
  03_hero_summary.csv        -- Hero meta stats (Ranked only)
  04_rank_current.csv        -- Rank hien tai cua tung player
  05_player_hero_pool.csv    -- Top 5 heroes cua tung player
  06_team_daily_last30.csv   -- KPI theo team, tung ngay, 30 ngay gan nhat
  07_player_daily_last30.csv -- KPI theo player, tung ngay, 30 ngay gan nhat

HUONG DAN TRA LOI:
  - Cau hoi ve "hom nay", "hom qua", "X ngay gan nhat" -> dung file 06 hoac 07
  - Cau hoi ve tong quat (WinRate, KDA...) -> dung file 01 hoac 02
  - Cau hoi ve hero -> dung file 03 hoac 05
  - Cau hoi ve rank -> dung file 04

KPI Definitions:
  WinRate_pct : % tran thang (weighted average)
  KDA         : (Kill + Assist) / Death; neu Death=0 thi = Kill+Assist
  MVPRate_pct : % tran dat MVP
  AvgDamage   : Damage trung binh moi tran
  AvgGold     : Gold trung binh moi tran
  AvgFarm     : Farm (minions) trung binh moi tran
  PlayerGames : Tong so luot choi (COUNT *)
  Matches     : So tran rieng biet (COUNT DISTINCT BattleID)
""")
print(f"  v 00_system_info.txt")

con.close()
print(f"\nDone! Files saved to: {OUT_DIR}")
