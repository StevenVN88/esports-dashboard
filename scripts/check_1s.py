import duckdb

DB_PATH = r"D:\EsportsAI\db\esports.duckdb"

con = duckdb.connect(DB_PATH)

query = """

SELECT
    Team,
    GameDate,
    SUM(PlayerGames) AS Games,
    SUM(UniqueMatches) AS Matches

FROM report_team_daily

WHERE Team = '1S'
AND GameDate BETWEEN '2026-05-20' AND '2026-05-26'

GROUP BY Team, GameDate

ORDER BY GameDate

"""

df = con.execute(query).fetchdf()

print(df)