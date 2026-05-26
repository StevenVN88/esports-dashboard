import duckdb

DB_PATH = r"D:\EsportsAI\db\esports.duckdb"

con = duckdb.connect(DB_PATH)

# ==========================================
# UNIFIED MATCH HISTORY
# ==========================================

con.execute("""

CREATE OR REPLACE VIEW mh_all AS

SELECT
    'VN' AS Server,
    *
FROM match_history_vn

UNION ALL

SELECT
    'TH' AS Server,
    *
FROM match_history_th

UNION ALL

SELECT
    'TW' AS Server,
    *
FROM match_history_tw

""")

# ==========================================
# UNIFIED BEHAVIOR
# ==========================================

con.execute("""

CREATE OR REPLACE VIEW behavior_all AS

SELECT
    'VN' AS Server,
    *
FROM behavior_info_vn

UNION ALL

SELECT
    'TH' AS Server,
    *
FROM behavior_info_th

UNION ALL

SELECT
    'TW' AS Server,
    *
FROM behavior_info_tw

""")

# ==========================================
# UNIFIED RANK
# ==========================================

con.execute("""

CREATE OR REPLACE VIEW rank_all AS

SELECT
    'VN' AS Server,
    *
FROM rank_before_after_vn

UNION ALL

SELECT
    'TH' AS Server,
    *
FROM rank_before_after_th

UNION ALL

SELECT
    'TW' AS Server,
    *
FROM rank_before_after_tw

""")

# ==========================================
# PLAYER ACCOUNT MAP
# ==========================================

con.execute("""

CREATE OR REPLACE VIEW player_accounts AS

SELECT
    Player,
    Team,
    Server,
    TencentID,
    Account
FROM uid_all

""")

print("Views created successfully.")