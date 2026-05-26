import duckdb

DB_PATH = r"D:\EsportsAI\db\esports.duckdb"

con = duckdb.connect(DB_PATH)

# =====================================================
# PLAYER DAILY REPORT (extended with Damage/Gold/Farm)
# =====================================================

con.execute("""

CREATE OR REPLACE VIEW report_player_daily AS

SELECT

    p.Player,
    p.Team,
    p.Server,
    p.Account,

    DATE(m.Date_Time) AS GameDate,

    COUNT(*) AS PlayerGames,

    COUNT(DISTINCT m.BattleID) AS UniqueMatches,

    SUM(
        CASE
            WHEN m.Game_Mode = 'Ranked'
            THEN 1
            ELSE 0
        END
    ) AS RankedGames,

    ROUND(
        SUM(
            CASE
                WHEN m.Game_Result = 'Win'
                THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        2
    ) AS WinRate,

    ROUND(
        AVG(
            CASE
                WHEN m.DeadCnt = 0
                THEN (m.KillCnt + m.AssistCnt)

                ELSE
                (m.KillCnt + m.AssistCnt)
                * 1.0 / m.DeadCnt
            END
        ),
        2
    ) AS KDA,

    ROUND(
        AVG(m.Is_MVP) * 100,
        2
    ) AS MVPRate,

    ROUND(AVG(m.Total_Damage), 0) AS AvgDamage,
    ROUND(AVG(m.Total_Gold), 0) AS AvgGold,
    ROUND(AVG(m.Total_Minions), 0) AS AvgFarm

FROM mh_all m

LEFT JOIN player_accounts p
ON m.TencentID = p.TencentID

WHERE p.Player IS NOT NULL

GROUP BY
    p.Player,
    p.Team,
    p.Server,
    p.Account,
    DATE(m.Date_Time)

""")

print("report_player_daily created.")

# =====================================================
# TEAM DAILY REPORT
# =====================================================

con.execute("""

CREATE OR REPLACE VIEW report_team_daily AS

SELECT

    p.Team,

    DATE(m.Date_Time) AS GameDate,

    COUNT(*) AS PlayerGames,

    COUNT(DISTINCT m.BattleID) AS UniqueMatches,

    ROUND(
        SUM(
            CASE
                WHEN m.Game_Result = 'Win'
                THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        2
    ) AS WinRate,

    ROUND(
        AVG(
            CASE
                WHEN m.DeadCnt = 0
                THEN (m.KillCnt + m.AssistCnt)

                ELSE
                (m.KillCnt + m.AssistCnt)
                * 1.0 / m.DeadCnt
            END
        ),
        2
    ) AS KDA

FROM mh_all m

LEFT JOIN player_accounts p
ON m.TencentID = p.TencentID

WHERE p.Team IS NOT NULL

GROUP BY
    p.Team,
    DATE(m.Date_Time)

""")

print("report_team_daily created.")

# =====================================================
# HERO DAILY REPORT (extended with Damage/Gold)
# =====================================================

con.execute("""

CREATE OR REPLACE VIEW report_hero_daily AS

SELECT

    h.HeroName,

    DATE(m.Date_Time) AS GameDate,

    COUNT(DISTINCT m.BattleID) AS UniqueMatches,

    ROUND(
        SUM(
            CASE
                WHEN m.Game_Result = 'Win'
                THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        2
    ) AS WinRate,

    ROUND(
        AVG(m.Is_MVP) * 100,
        2
    ) AS MVPRate,

    ROUND(AVG(m.Total_Damage), 0) AS AvgDamage,
    ROUND(AVG(m.Total_Gold), 0) AS AvgGold

FROM mh_all m

LEFT JOIN hero h
ON m.Hero = h.HeroID

WHERE m.Game_Mode = 'Ranked'
AND h.HeroName IS NOT NULL

GROUP BY
    h.HeroName,
    DATE(m.Date_Time)

""")

print("report_hero_daily created.")

# =====================================================
# PLAYER HERO REPORT (for Player Detail tab)
# =====================================================

con.execute("""

CREATE OR REPLACE VIEW report_player_hero AS

SELECT

    p.Player,
    p.Team,
    p.Server,

    h.HeroName,

    DATE(m.Date_Time) AS GameDate,

    COUNT(*) AS PlayerGames,

    ROUND(
        SUM(
            CASE
                WHEN m.Game_Result = 'Win'
                THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        2
    ) AS WinRate,

    ROUND(
        AVG(
            CASE
                WHEN m.DeadCnt = 0
                THEN (m.KillCnt + m.AssistCnt)

                ELSE
                (m.KillCnt + m.AssistCnt)
                * 1.0 / m.DeadCnt
            END
        ),
        2
    ) AS KDA,

    ROUND(
        AVG(m.Is_MVP) * 100,
        2
    ) AS MVPRate

FROM mh_all m

LEFT JOIN player_accounts p
ON m.TencentID = p.TencentID

LEFT JOIN hero h
ON m.Hero = h.HeroID

WHERE p.Player IS NOT NULL
AND h.HeroName IS NOT NULL

GROUP BY
    p.Player,
    p.Team,
    p.Server,
    h.HeroName,
    DATE(m.Date_Time)

""")

print("report_player_hero created.")

# =====================================================
# MATCH HISTORY (row-level, NO aggregation)
# =====================================================

con.execute("""

CREATE OR REPLACE VIEW report_match_history AS

SELECT

    p.Player,
    p.Team,
    p.Server,
    p.Account,

    m.Date_Time,
    m.BattleID,

    h.HeroName,

    m.Game_Mode,
    m.Game_Result,
    m.Team_Side,
    m.Team_Size,

    ROUND(m.Match_Duration / 60.0, 2) AS MatchMinutes,

    m.KillCnt,
    m.DeadCnt,
    m.AssistCnt,

    m.Total_Damage,
    m.Total_Damage_Received,
    m.Total_Gold,
    m.Total_Minions,
    m.DestoryTowerCnt,
    m.Hero_Level,
    m.Is_MVP

FROM mh_all m

LEFT JOIN player_accounts p
ON m.TencentID = p.TencentID

LEFT JOIN hero h
ON m.Hero = h.HeroID

WHERE p.Player IS NOT NULL

""")

print("report_match_history created.")

# =====================================================
# INACTIVE PLAYER REPORT
# =====================================================

con.execute("""

CREATE OR REPLACE VIEW report_inactive_players AS

SELECT

    Player,
    Team,
    Server,
    Account,

    LastGameDate,

    DATE_DIFF(
        'day',
        LastGameDate,
        CURRENT_DATE
    ) AS InactiveDays

FROM core_player_summary

""")

print("report_inactive_players created.")

# =====================================================
# BEHAVIOR REPORT
# =====================================================

con.execute("""

CREATE OR REPLACE VIEW report_behavior AS

SELECT

    p.Player,
    p.Team,
    p.Server,

    DATE(b.Date_Time) AS GameDate,

    COUNT(*) AS TotalReports,

    SUM(CAST(b.AFK AS INT))           AS AFK,
    SUM(CAST(b.Feeding AS INT))       AS Feeding,
    SUM(CAST(b.Bad_Words AS INT))     AS Bad_Words,
    SUM(CAST(b.Sabotage AS INT))      AS Sabotage,
    SUM(CAST(b.Lane_Stealing AS INT)) AS Lane_Stealing,
    SUM(CAST(b.Hack AS INT))          AS Hack

FROM behavior_all b

LEFT JOIN player_accounts p
ON b.ReportedOpenID = p.TencentID

WHERE p.Player IS NOT NULL

GROUP BY
    p.Player,
    p.Team,
    p.Server,
    DATE(b.Date_Time)

""")

print("report_behavior created.")
print("\nAll reporting views created successfully.")