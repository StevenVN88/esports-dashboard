import duckdb

DB_PATH = r"D:\EsportsAI\db\esports.duckdb"

con = duckdb.connect(DB_PATH)

query = """

SELECT
    p.Player,
    h.HeroName,
    COUNT(*) AS Games

FROM mh_all m

LEFT JOIN player_accounts p
ON m.TencentID = p.TencentID

LEFT JOIN hero h
ON m.Hero = h.HeroID

WHERE p.Player = 'Tama'

GROUP BY
    p.Player,
    h.HeroName

ORDER BY Games DESC

LIMIT 20

"""
df = con.execute(query).fetchdf()

print(df)