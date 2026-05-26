import duckdb

DB_PATH = r"D:\EsportsAI\db\esports.duckdb"

con = duckdb.connect(DB_PATH)

query = """

SELECT
    Team,
    MIN(GameDate) AS MinDate,
    MAX(GameDate) AS MaxDate,
    SUM(PlayerGames) AS Games

FROM report_team_daily

GROUP BY Team

ORDER BY MaxDate DESC

"""

df = con.execute(query).fetchdf()

print(df)