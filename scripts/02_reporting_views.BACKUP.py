import duckdb

DB_PATH = r"D:\EsportsAI\db\esports.duckdb"

con = duckdb.connect(DB_PATH)

# =====================================================
# PLAYER DAILY REPORT
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
    ) AS MVPRate

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

# =====================================================
# HERO DAILY REPORT
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
    ) AS MVPRate

FROM mh_all m

LEFT JOIN hero h
ON m.Hero = h.HeroID

WHERE m.Game_Mode = 'Ranked'
AND h.HeroName IS NOT NULL

GROUP BY
    h.HeroName,
    DATE(m.Date_Time)

""")

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

print("Reporting views created successfully.")
