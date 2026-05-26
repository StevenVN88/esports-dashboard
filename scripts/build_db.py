import duckdb
import pandas as pd
from pathlib import Path

DATA_DIR = Path(r"D:\EsportsAI\data")
DB_PATH = r"D:\EsportsAI\db\esports.duckdb"

con = duckdb.connect(DB_PATH)

FILES = {
    "hero": "hero.csv",
    "rankmapping": "rankmapping.csv",
    "uid_all": "uid_all.csv",

    "match_history_vn": "match_history_vn.csv",
    "match_history_th": "match_history_th.csv",
    "match_history_tw": "match_history_tw.csv",

    "behavior_info_vn": "behavior_info_vnnew.csv",
    "behavior_info_th": "behavior_info_thnew.csv",
    "behavior_info_tw": "behavior_info_twnew.csv",

    "rank_before_after_vn": "rank_before_after_raw_vn.csv",
    "rank_before_after_th": "rank_before_after_raw_th.csv",
    "rank_before_after_tw": "rank_before_after_raw_tw.csv"
}

for table_name, file_name in FILES.items():

    file_path = DATA_DIR / file_name

    print(f"Loading {file_name}...")

    df = pd.read_csv(file_path)

    con.execute(f"DROP TABLE IF EXISTS {table_name}")

    con.register("temp_df", df)

    con.execute(f"""
        CREATE TABLE {table_name} AS
        SELECT * FROM temp_df
    """)

    print(f"Imported: {table_name}")

print("\nDONE")
print(f"Database saved at: {DB_PATH}")