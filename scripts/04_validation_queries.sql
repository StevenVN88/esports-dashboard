-- =====================================================
-- VALIDATION 01
-- CHECK TOTAL ROWS
-- =====================================================

SELECT
    COUNT(*) AS TotalRows
FROM mh_all;


-- =====================================================
-- VALIDATION 02
-- CHECK UNIQUE MATCHES
-- =====================================================

SELECT
    COUNT(DISTINCT BattleID) AS UniqueMatches
FROM mh_all;


-- =====================================================
-- VALIDATION 03
-- CHECK PLAYER GAME COUNT
-- EXAMPLE: KARL
-- =====================================================

SELECT

    p.Player,
    COUNT(*) AS PlayerGames

FROM mh_all m

LEFT JOIN player_accounts p
ON m.TencentID = p.TencentID

WHERE p.Player = 'Karl'

GROUP BY p.Player;


-- =====================================================
-- VALIDATION 04
-- CHECK PLAYER GAMES IN DATE RANGE
-- =====================================================

SELECT

    p.Player,
    COUNT(*) AS PlayerGames

FROM mh_all m

LEFT JOIN player_accounts p
ON m.TencentID = p.TencentID

WHERE p.Player = 'Karl'

AND DATE(m.Date_Time)
BETWEEN '2026-04-01'
AND '2026-05-18'

GROUP BY p.Player;


-- =====================================================
-- VALIDATION 05
-- CHECK UNIQUE MATCHES IN DATE RANGE
-- =====================================================

SELECT

    COUNT(DISTINCT BattleID) AS UniqueMatches

FROM mh_all

WHERE DATE(Date_Time)
BETWEEN '2026-04-01'
AND '2026-05-18';


-- =====================================================
-- VALIDATION 06
-- CHECK TEAM PLAYER GAMES
-- =====================================================

SELECT

    p.Team,
    COUNT(*) AS PlayerGames

FROM mh_all m

LEFT JOIN player_accounts p
ON m.TencentID = p.TencentID

WHERE p.Team = '1S'

AND DATE(m.Date_Time)
BETWEEN '2026-04-01'
AND '2026-05-18'

GROUP BY p.Team;


-- =====================================================
-- VALIDATION 07
-- CHECK TEAM UNIQUE MATCHES
-- =====================================================

SELECT

    p.Team,
    COUNT(DISTINCT m.BattleID) AS UniqueMatches

FROM mh_all m

LEFT JOIN player_accounts p
ON m.TencentID = p.TencentID

WHERE p.Team = '1S'

AND DATE(m.Date_Time)
BETWEEN '2026-04-01'
AND '2026-05-18'

GROUP BY p.Team;


-- =====================================================
-- VALIDATION 08
-- CHECK HERO MATCH COUNT
-- =====================================================

SELECT

    h.HeroName,
    COUNT(DISTINCT m.BattleID) AS Matches

FROM mh_all m

LEFT JOIN hero h
ON m.Hero = h.HeroID

WHERE h.HeroName = 'Airi'

AND DATE(m.Date_Time)
BETWEEN '2026-04-01'
AND '2026-05-18'

GROUP BY h.HeroName;


-- =====================================================
-- VALIDATION 09
-- CHECK HERO PLAYER COUNT
-- =====================================================

SELECT

    h.HeroName,
    COUNT(*) AS PlayerGames

FROM mh_all m

LEFT JOIN hero h
ON m.Hero = h.HeroID

WHERE h.HeroName = 'Airi'

AND DATE(m.Date_Time)
BETWEEN '2026-04-01'
AND '2026-05-18'

GROUP BY h.HeroName;


-- =====================================================
-- VALIDATION 10
-- CHECK RANK LATEST DUPLICATES
-- SHOULD RETURN 0 ROWS
-- =====================================================

SELECT

    TencentID,
    COUNT(*) AS Cnt

FROM (

    SELECT
        TencentID,
        ROW_NUMBER() OVER (
            PARTITION BY TencentID
            ORDER BY Date_Time DESC
        ) AS rn

    FROM rank_all

)

WHERE rn = 1

GROUP BY TencentID

HAVING COUNT(*) > 1;


-- =====================================================
-- VALIDATION 11
-- CHECK CURRENT RANK
-- EXAMPLE: STARK
-- =====================================================

SELECT *

FROM core_rank_latest

WHERE Player = 'Stark';


-- =====================================================
-- VALIDATION 12
-- CHECK MVP RATE
-- =====================================================

SELECT

    p.Player,

    ROUND(
        AVG(m.Is_MVP) * 100,
        2
    ) AS MVPRate

FROM mh_all m

LEFT JOIN player_accounts p
ON m.TencentID = p.TencentID

WHERE p.Player = 'Karl'

GROUP BY p.Player;


-- =====================================================
-- VALIDATION 13
-- CHECK SAFE KDA
-- =====================================================

SELECT

    p.Player,

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

WHERE p.Player = 'Karl'

GROUP BY p.Player;


-- =====================================================
-- VALIDATION 14
-- CHECK HERO META RANKED ONLY
-- =====================================================

SELECT

    h.HeroName,
    COUNT(DISTINCT m.BattleID) AS Matches

FROM mh_all m

LEFT JOIN hero h
ON m.Hero = h.HeroID

WHERE m.Game_Mode = 'Ranked'

GROUP BY h.HeroName

ORDER BY Matches DESC

LIMIT 20;


-- =====================================================
-- VALIDATION 15
-- CHECK INACTIVE PLAYERS
-- =====================================================

SELECT *

FROM report_inactive_players

ORDER BY InactiveDays DESC

LIMIT 20;