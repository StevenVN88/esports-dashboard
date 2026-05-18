# ESPORTS ANALYTICS SYSTEM
# FINAL ARCHITECTURE SPECIFICATION

---

# 1. SYSTEM PURPOSE

This system is an esports performance intelligence platform designed to analyze:

- Teams
- Players
- Accounts
- Heroes
- Ranked progression
- Training activity

Across multiple game servers:

- VN
- TH
- TW

The system supports:

- Dashboard analytics
- Team owner reports
- Coaching analysis
- AI summaries
- Future online deployment

---

# 2. CORE ARCHITECTURE

RAW TABLES
↓
CORE VIEWS
↓
REPORTING VIEWS
↓
APP.PY (UI)
↓
CLAUDE AI

---

# 3. RAW TABLES

## MATCH DATA
mh_all

Contains:
- BattleID
- TencentID
- Date_Time
- Hero
- Game_Result
- Is_MVP
- Game_Mode
- Match_Duration
- Team_Size
- KillCnt
- DeadCnt
- AssistCnt

1 ROW = 1 PLAYER PARTICIPATION IN 1 MATCH

---

## PLAYER MAPPING
player_accounts

Contains:
- Player
- Team
- Server
- TencentID
- Account

Used as:
- roster mapping
- team mapping
- account ownership

---

## RANK DATA
rank_all

Contains:
- Rank_Before
- Star_Before
- Rank_After
- Star_After
- Date_Time

Rank latest is determined by:
ROW_NUMBER() OVER (
PARTITION BY TencentID
ORDER BY Date_Time DESC
)

---

## HERO DATA
hero

Contains:
- HeroID
- HeroName

Used for:
Hero mapping.

---

# 4. CORE LOGIC RULES

## PLAYER GAMES

Use:

COUNT(*)

Reason:
1 row = 1 player participation.

This measures:
- workload
- activity
- training intensity

---

## UNIQUE MATCHES

Use:

COUNT(DISTINCT BattleID)

Reason:
1 BattleID = 1 actual match.

Used for:
- hero analytics
- team match analytics
- true match counts

---

## WINRATE

Formula:

Win / TotalGames

SQL:

SUM(
CASE WHEN Game_Result='Win'
THEN 1 ELSE 0 END
)
/
COUNT(*)

---

## SAFE KDA

Formula:

(Kills + Assists) / Deaths

BUT:

If DeadCnt = 0:
Use:
Kills + Assists

NEVER divide by zero.

---

## MVP RATE

Formula:

AVG(Is_MVP) * 100

Reason:
Is_MVP values:
- 0
- 1

---

## HERO DIVERSITY

Formula:

COUNT(DISTINCT Hero)

Measures:
- hero pool width
- flexibility

---

## HERO ANALYTICS

MUST use:

WHERE Game_Mode='Ranked'

Reason:
Normal games distort meta analytics.

---

## MATCH DURATION

Stored in:
seconds

Dashboard displays:
minutes

Formula:

AVG(Match_Duration) / 60

---

# 5. RANK SYSTEM

## Rank Logic

Rank = Rank_After + Star_After

NOT Rank_After only.

---

## Latest Rank

Always use:
latest Date_Time per TencentID.

NEVER show full history in overview dashboards.

---

## Rank Mapping

### Rank_After Mapping

1 = Đồng 3
2 = Đồng 2
...
15 = BK 1

### Additional Grade Mapping

17 = Vàng 4
18 = BK 5
19 = BK 4
20 = KC 5
21 = KC 4
22 = Tinh Anh 5
23 = Tinh Anh 4
24 = Tinh Anh 3
25 = Tinh Anh 2
26 = Tinh Anh 1

### Special Rank Logic

Rank_After = 16:
Use Star_After:

0-9 = Cao Thủ
10-19 = Đại Cao Thủ 4
20-29 = Đại Cao Thủ 3
30-39 = Đại Cao Thủ 2
40-49 = Đại Cao Thủ 1

27 = Chiến Tướng 50*+
28 = Đại Cao Thủ 4 (alt path)
29 = Đại Cao Thủ 3 (alt path)
30 = Đại Cao Thủ 2 (alt path)
31 = Đại Cao Thủ 1 (alt path)
32 = Chiến Thần 100*+

---

# 6. REPORTING LAYER RULES

REPORTING VIEWS:
- report_player_daily
- report_team_daily
- report_hero_daily
- report_inactive_players

These are:
DATETIME-AWARE.

---

# 7. UI RULES

## APP.PY MUST:

ONLY query:
- core_*
- report_*

views.

---

## APP.PY MUST NEVER:

- query raw tables directly
- duplicate KPI formulas
- calculate business logic in UI layer

---

# 8. GLOBAL FILTERS

Dashboard global filters:

- Team
- Server
- Start Date
- End Date

Optional future:
- Player Mode

---

# 9. PLAYER ANALYTICS RULES

Players tab must show:

## ALL PLAYERS
- workload
- WR
- KDA
- MVP
- hero diversity

AND:

## PLAYER DRILLDOWN
- timeline
- hero pool
- rank
- activity

---

# 10. HERO ANALYTICS RULES

Heroes tab must show:

- Matches
- WinRate
- MVP Rate
- Top Players
- Top Teams
- Hero Trend

Hero analytics MUST use:
UniqueMatches

NOT player rows.

---

# 11. TEAM ANALYTICS RULES

Overview tab must show:

- Team KPI
- Timeline
- Top Players
- Hero Pool
- Rank Distribution

---

# 12. TIMEZONE RULES

System timezone:
Asia/Ho_Chi_Minh

All reporting should follow Vietnam timezone logic.

---

# 13. AI RULES

Claude AI may:
- refactor UI
- improve UX
- add charts
- improve deployment

Claude AI must NOT:
- rewrite KPI logic
- duplicate formulas
- bypass reporting views
- query raw tables in UI layer

---

# 14. DEPLOYMENT RULES

Recommended deployment:
- Streamlit Cloud
- Railway
- VPS later

NOT recommended:
multiple duplicated dashboards.

Use:
1 codebase
1 database
multiple filtered views.

---

# 15. FUTURE FEATURES

Allowed:
- Plotly
- Auth
- AI summaries
- PDF reports
- Weekly reports
- Behavior analytics

Avoid:
- MMR prediction
- Hero recommendation AI
- Matchmaking prediction

Until architecture stabilizes.

---

# 16. SOURCE OF TRUTH

The SOURCE OF TRUTH for all analytics is:

- CORE VIEWS
- REPORTING VIEWS

NOT:
- app.py
- ad-hoc queries
- UI calculations

---

# END OF SPECIFICATION