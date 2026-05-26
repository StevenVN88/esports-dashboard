import duckdb

DB_PATH = r"D:\EsportsAI\db\esports.duckdb"

con = duckdb.connect(DB_PATH)

# =====================================================
# PLAYER SUMMARY VIEW
# =====================================================

con.execute("""

CREATE OR REPLACE VIEW view_player_summary AS

SELECT

    p.Player,
    p.Team,
    p.Server,
    p.Account,

    COUNT(*) AS TotalGames,

    SUM(
        CASE
            WHEN m.Game_Mode = 'Ranked'
            THEN 1
            ELSE 0
        END
    ) AS RankedGames,

    SUM(
        CASE
            WHEN m.Game_Mode = 'Normal'
            THEN 1
            ELSE 0
        END
    ) AS NormalGames,

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
        SUM(
            CASE
                WHEN m.Game_Result = 'Win'
                AND m.Game_Mode = 'Ranked'
                THEN 1
                ELSE 0
            END
        ) * 100.0 /
        NULLIF(
            SUM(
                CASE
                    WHEN m.Game_Mode = 'Ranked'
                    THEN 1
                    ELSE 0
                END
            ),
            0
        ),
        2
    ) AS RankedWinRate,

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

    ROUND(
        AVG(m.Match_Duration) / 60,
        2
    ) AS AvgMatchMinutes,

    ROUND(
        AVG(m.KillCnt),
        2
    ) AS AvgKills,

    ROUND(
        AVG(m.DeadCnt),
        2
    ) AS AvgDeaths,

    ROUND(
        AVG(m.AssistCnt),
        2
    ) AS AvgAssists,

    COUNT(
        DISTINCT m.Hero
    ) AS HeroDiversity,

    MIN(DATE(m.Date_Time)) AS FirstGameDate,
    MAX(DATE(m.Date_Time)) AS LastGameDate,

    ROUND(
        COUNT(*) * 1.0 /
        NULLIF(
            COUNT(
                DISTINCT DATE(m.Date_Time)
            ),
            0
        ),
        2
    ) AS AvgGamesPerDay

FROM mh_all m

LEFT JOIN player_accounts p
ON m.TencentID = p.TencentID

WHERE p.Player IS NOT NULL

GROUP BY
    p.Player,
    p.Team,
    p.Server,
    p.Account

""")

# =====================================================
# PLAYER DAILY HISTORY
# =====================================================

con.execute("""

CREATE OR REPLACE VIEW view_player_daily_history AS

SELECT

    p.Player,
    p.Team,
    p.Server,
    p.Account,

    DATE(m.Date_Time) AS GameDate,

    COUNT(*) AS Games,

    ROUND(
        SUM(
            CASE
                WHEN m.Game_Result = 'Win'
                THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        2
    ) AS WinRate

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
# TEAM SUMMARY VIEW
# =====================================================

con.execute("""

CREATE OR REPLACE VIEW view_team_summary AS

SELECT

    p.Team,

    COUNT(*) AS TotalGames,

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

    ROUND(
        AVG(m.Match_Duration) / 60,
        2
    ) AS AvgMatchMinutes,

    COUNT(
        DISTINCT p.Player
    ) AS ActivePlayers,

    COUNT(
        DISTINCT m.Hero
    ) AS HeroDiversity

FROM mh_all m

LEFT JOIN player_accounts p
ON m.TencentID = p.TencentID

WHERE p.Team IS NOT NULL

GROUP BY p.Team

""")

# =====================================================
# TEAM ROSTER VIEW
# =====================================================

con.execute("""

CREATE OR REPLACE VIEW view_team_roster AS

SELECT DISTINCT

    Team,
    Player,
    Server,
    Account

FROM player_accounts

WHERE Team IS NOT NULL

""")

# =====================================================
# RANK VIEW
# =====================================================

con.execute("""

CREATE OR REPLACE VIEW view_player_rank AS

SELECT

    p.Player,
    p.Team,
    p.Server,

    r.Rank_After,
    r.Star_After,

    CASE

        WHEN r.Rank_After = 1 THEN '01 - Đồng 3'
        WHEN r.Rank_After = 2 THEN '02 - Đồng 2'
        WHEN r.Rank_After = 3 THEN '03 - Đồng 1'
        WHEN r.Rank_After = 4 THEN '04 - Bạc 3'
        WHEN r.Rank_After = 5 THEN '05 - Bạc 2'
        WHEN r.Rank_After = 6 THEN '06 - Bạc 1'
        WHEN r.Rank_After = 7 THEN '07 - Vàng 4'
        WHEN r.Rank_After = 8 THEN '08 - Vàng 3'
        WHEN r.Rank_After = 9 THEN '09 - Vàng 2'
        WHEN r.Rank_After = 10 THEN '10 - Vàng 1'
        WHEN r.Rank_After = 11 THEN '11 - BK 5'
        WHEN r.Rank_After = 12 THEN '12 - BK 4'
        WHEN r.Rank_After = 13 THEN '13 - BK 3'
        WHEN r.Rank_After = 14 THEN '14 - BK 2'
        WHEN r.Rank_After = 15 THEN '15 - BK 1'

        WHEN r.Rank_After = 16 THEN
            CASE
                WHEN r.Star_After BETWEEN 0 AND 9 THEN '26a - Cao Thủ'
                WHEN r.Star_After BETWEEN 10 AND 19 THEN '26b - Đại Cao Thủ 4'
                WHEN r.Star_After BETWEEN 20 AND 29 THEN '26c - Đại Cao Thủ 3'
                WHEN r.Star_After BETWEEN 30 AND 39 THEN '26d - Đại Cao Thủ 2'
                WHEN r.Star_After BETWEEN 40 AND 49 THEN '26e - Đại Cao Thủ 1'
            END

        WHEN r.Rank_After = 27 THEN '27 - Chiến Tướng 50*+'
        WHEN r.Rank_After = 32 THEN '28 - Chiến Thần 100*+'

        ELSE 'Unknown'

    END AS RankName,

    MAX(r.Date_Time) AS LastRankUpdate

FROM rank_all r

LEFT JOIN player_accounts p
ON r.TencentID = p.TencentID

WHERE p.Player IS NOT NULL

GROUP BY
    p.Player,
    p.Team,
    p.Server,
    r.Rank_After,
    r.Star_After

""")

print("Analytics views created successfully.")