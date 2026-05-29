"""
ADMIN PANEL — LOCAL ONLY
Chạy: streamlit run dashboard/admin.py

Flow: Upload CSV → Merge vào data cũ → Rebuild DuckDB → Git push (Streamlit Cloud tự rebuild).
CHỈ chạy LOCAL. DB: D:\\EsportsAI\\db\\esports.duckdb
"""

import streamlit as st
import pandas as pd
import duckdb
import os
import sys
import subprocess
import random
import string
from datetime import datetime

# =====================================================
# CONFIG
# =====================================================

ADMIN_PASSWORD = "esports2024"          # local-only gate, no secrets needed

REPO_DIR = r"D:\EsportsAI"
DATA_DIR = os.path.join(REPO_DIR, "data")
DB_PATH = os.path.join(REPO_DIR, "db", "esports.duckdb")

# Team access — team_app.py reads tokens from .streamlit/team_tokens.toml
TOML_PATH = os.path.join(REPO_DIR, ".streamlit", "team_tokens.toml")
TEAM_APP_URL = "https://aovteam.streamlit.app"
TEAM_ORDER = ["BOX", "FPT", "SGP", "SPN", "FPL", "1S", "GAM", "TS"]

# EXACT same config as scripts/merge_csv.py
MERGE_CONFIG = {
    "match_history_vn.csv":         ["BattleID", "TencentID"],
    "match_history_th.csv":         ["BattleID", "TencentID"],
    "match_history_tw.csv":         ["BattleID", "TencentID"],
    "rank_before_after_raw_vn.csv": ["BattleID", "TencentID", "Date_Time"],
    "rank_before_after_raw_th.csv": ["BattleID", "TencentID", "Date_Time"],
    "rank_before_after_raw_tw.csv": ["BattleID", "TencentID", "Date_Time"],
    "behavior_info_vnnew.csv":      ["BattleID", "ReportedOpenID", "Date_Time"],
    "behavior_info_thnew.csv":      ["BattleID", "ReportedOpenID", "Date_Time"],
    "behavior_info_twnew.csv":      ["BattleID", "ReportedOpenID", "Date_Time"],
    "uid_all.csv":                  ["TencentID"],
    "hero.csv":                     ["HeroID"],
}

# Same order as UPDATE_DATA.bat (steps 1→4; merge handled in-app)
REBUILD_STEPS = [
    ("build_db.py",          "Rebuild Database từ CSV"),
    ("build_views.py",       "Tạo base views (mh_all, rank_all, behavior_all, player_accounts)"),
    ("01_core_views.py",     "Tạo core views (player_summary, team_summary, rank_latest)"),
    ("02_reporting_views.py","Tạo reporting views (daily reports, hero, behavior)"),
]

# Never-truncate guard tables
SAFETY_TABLES = ["mh_all", "rank_all"]

COLORS = {
    "primary": "#6c5ce7", "success": "#00cec9", "warning": "#fdcb6e",
    "danger": "#e17055", "info": "#74b9ff", "accent": "#a29bfe",
}

st.set_page_config(page_title="Admin — Esports Analytics", page_icon="🛠️", layout="wide")

# =====================================================
# CUSTOM CSS (same dark theme as app.py)
# =====================================================

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Be Vietnam Pro', sans-serif; }

    .kpi-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px; padding: 16px 20px; border-left: 4px solid; margin-bottom: 8px;
    }
    .kpi-card .kpi-label {
        font-size: 12px; font-weight: 600; text-transform: uppercase;
        letter-spacing: 1.2px; color: #8888aa; margin-bottom: 4px;
    }
    .kpi-card .kpi-value { font-size: 26px; font-weight: 800; color: #e0e0ff; line-height: 1.1; }
    .kpi-card .kpi-sub { font-size: 11px; color: #6a6a8a; margin-top: 4px; }

    .section-header {
        font-size: 16px; font-weight: 700; color: #c0c0e0; letter-spacing: 0.5px;
        padding-bottom: 8px; border-bottom: 2px solid #2a2a4a; margin: 24px 0 16px 0;
    }
    .lock-note { color: #6a6a8a; font-size: 13px; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# HELPERS (same as app.py)
# =====================================================

def kpi_card(label, value, sub="", color="#6c5ce7"):
    return f"""
    <div class="kpi-card" style="border-left-color: {color};">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """

def section_header(text):
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)

def detect_file_type(filename):
    """Map an uploaded filename to a canonical MERGE_CONFIG key (exact match only)."""
    name = os.path.basename(filename).lower()
    for key in MERGE_CONFIG:
        if name == key.lower():
            return key
    return None

def db_counts():
    """Read-only row counts for the safety tables. Connection closed immediately."""
    counts = {}
    try:
        c = duckdb.connect(DB_PATH, read_only=True)
        for t in SAFETY_TABLES:
            try:
                counts[t] = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except Exception:
                counts[t] = None
        c.close()
    except Exception as e:
        counts["_error"] = str(e)
    return counts

def run_script(script):
    """Run a pipeline script with the SAME interpreter running Streamlit."""
    proc = subprocess.run(
        [sys.executable, os.path.join("scripts", script)],
        cwd=REPO_DIR, capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr

def run_git(args):
    proc = subprocess.run(["git"] + args, cwd=REPO_DIR, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr

def gen_token():
    return "".join(random.choices(string.ascii_letters + string.digits, k=11))

def merge_uploaded(filename, df_new):
    """EXACT merge logic from scripts/merge_csv.py, on an in-memory new df."""
    keys = MERGE_CONFIG[filename]
    old_path = os.path.join(DATA_DIR, filename)
    stats = {"file": filename, "keys": keys, "new": len(df_new),
             "old": 0, "dupes": 0, "final": 0, "backup": None}
    if os.path.exists(old_path):
        df_old = pd.read_csv(old_path)
        stats["old"] = len(df_old)
        df_merged = pd.concat([df_old, df_new], ignore_index=True)
        before = len(df_merged)
        df_merged = df_merged.drop_duplicates(subset=keys, keep="last")
        stats["dupes"] = before - len(df_merged)
        backup_path = old_path.replace(".csv", f"_backup_{datetime.now().strftime('%Y%m%d')}.csv")
        os.rename(old_path, backup_path)         # backup BEFORE overwrite
        stats["backup"] = os.path.basename(backup_path)
    else:
        df_merged = df_new
    df_merged.to_csv(old_path, index=False)
    stats["final"] = len(df_merged)
    return stats

# =====================================================
# AUTH GATE
# =====================================================

if "admin_auth" not in st.session_state:
    st.session_state["admin_auth"] = False

if not st.session_state["admin_auth"]:
    st.title("🛠️ Admin Panel")
    st.caption("Trang quản trị LOCAL — cập nhật dữ liệu và đẩy lên GitHub.")
    pw = st.text_input("Mật khẩu admin", type="password")
    if st.button("Đăng nhập", use_container_width=True):
        if pw == ADMIN_PASSWORD:
            st.session_state["admin_auth"] = True
            st.rerun()
        else:
            st.error("Sai mật khẩu.")
    st.stop()

# init flow flags
for flag in ("merge_done", "rebuild_done"):
    st.session_state.setdefault(flag, False)

st.title("🛠️ Admin Panel — Cập Nhật Dữ Liệu")
st.caption(f"DB: `{DB_PATH}`  •  Repo: `{REPO_DIR}`")
st.warning("⚠️ Đóng dashboard chính (app.py) trước khi Rebuild để tránh khóa file DB.")

# =====================================================
# SECTION 1 — UPLOAD & MERGE
# =====================================================

section_header("1️⃣ Upload & Merge CSV")

uploaded = st.file_uploader(
    "Chọn file CSV mới (chỉ chứa DATA MỚI — sẽ gộp với data cũ)",
    type=["csv"], accept_multiple_files=True,
)

detected = []
if uploaded:
    for uf in uploaded:
        ftype = detect_file_type(uf.name)
        detected.append((uf, ftype))
        with st.expander(f"📄 {uf.name}  →  {ftype or '❓ KHÔNG NHẬN DẠNG ĐƯỢC'}", expanded=False):
            if ftype:
                st.markdown(f"**Merge keys:** `{MERGE_CONFIG[ftype]}`  •  **Lưu vào:** `data/{ftype}`")
            else:
                st.error("Tên file không khớp MERGE_CONFIG — file này sẽ bị bỏ qua.")
            try:
                uf.seek(0)
                st.dataframe(pd.read_csv(uf, nrows=5), use_container_width=True)
            except Exception as e:
                st.error(f"Không đọc được file: {e}")

    valid = [(uf, t) for uf, t in detected if t]
    if valid and st.button("✅ Xác nhận Merge", type="primary", use_container_width=True):
        results = []
        for uf, ftype in valid:
            try:
                uf.seek(0)
                df_new = pd.read_csv(uf)
                results.append(merge_uploaded(ftype, df_new))
            except Exception as e:
                results.append({"file": ftype, "error": str(e)})
        st.session_state["merge_results"] = results
        st.session_state["merge_done"] = True
        st.session_state["rebuild_done"] = False   # data changed → force re-rebuild
        st.rerun()

if st.session_state.get("merge_results"):
    st.markdown("##### Kết quả merge")
    for r in st.session_state["merge_results"]:
        if "error" in r:
            st.error(f"❌ {r['file']}: {r['error']}")
            continue
        st.markdown(f"**{r['file']}** — backup: `{r['backup'] or '(không có file cũ)'}`")
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(kpi_card("Rows cũ", f"{r['old']:,}", "", COLORS["info"]), unsafe_allow_html=True)
        c2.markdown(kpi_card("Rows mới", f"{r['new']:,}", "", COLORS["primary"]), unsafe_allow_html=True)
        c3.markdown(kpi_card("Trùng loại", f"{r['dupes']:,}", "keep=last", COLORS["warning"]), unsafe_allow_html=True)
        c4.markdown(kpi_card("Kết quả", f"{r['final']:,}", "rows cuối", COLORS["success"]), unsafe_allow_html=True)
    if st.session_state["merge_done"]:
        st.success("✅ Merge hoàn tất. Chuyển sang bước Rebuild DB.")

# =====================================================
# SECTION 2 — REBUILD DB
# =====================================================

section_header("2️⃣ Rebuild Database")

if not st.session_state["merge_done"]:
    st.markdown('<div class="lock-note">🔒 Hoàn tất bước 1 (Merge) để mở khóa.</div>', unsafe_allow_html=True)
else:
    before = db_counts()
    if "_error" not in before:
        st.markdown("##### Row counts TRƯỚC khi rebuild")
        cols = st.columns(len(SAFETY_TABLES))
        for col, t in zip(cols, SAFETY_TABLES):
            v = before.get(t)
            col.markdown(kpi_card(t, f"{v:,}" if isinstance(v, int) else "N/A", "", COLORS["info"]),
                         unsafe_allow_html=True)
    else:
        st.info(f"Chưa đọc được DB hiện tại ({before['_error']}). Có thể DB đang bị khóa hoặc chưa tồn tại.")

    try:
        test_con = duckdb.connect(DB_PATH, read_only=False)
        test_con.close()
    except Exception as e:
        st.error(f"⛔ DB đang bị lock bởi tiến trình khác (app.py đang chạy?): {e}")
        st.error("Đóng dashboard chính trước khi rebuild.")
        st.stop()
    st.success("✅ DB không bị lock, sẵn sàng rebuild.")

    if st.button("✅ Xác nhận Rebuild DB", type="primary", use_container_width=True):
        prog = st.progress(0.0, text="Bắt đầu...")
        n = len(REBUILD_STEPS)
        failed = False
        for i, (script, label) in enumerate(REBUILD_STEPS):
            prog.progress(i / n, text=f"[{i+1}/{n}] {label}...")
            rc, out, err = run_script(script)
            ok = rc == 0
            with st.expander(f"[{i+1}/{n}] {script} — {'✅ OK' if ok else '❌ LỖI'}", expanded=not ok):
                if out:
                    st.code(out)
                if err:
                    st.code(err)
            if not ok:
                prog.progress((i + 1) / n, text="Thất bại")
                st.error(f"❌ Bước `{script}` thất bại (exit {rc}). Dừng pipeline.")
                failed = True
                break
        if not failed:
            prog.progress(1.0, text="Hoàn tất!")
            after = db_counts()
            st.markdown("##### Row counts SAU khi rebuild")
            cols = st.columns(len(SAFETY_TABLES))
            warn = False
            for col, t in zip(cols, SAFETY_TABLES):
                bv, av = before.get(t), after.get(t)
                sub = ""
                color = COLORS["success"]
                if isinstance(bv, int) and isinstance(av, int):
                    delta = av - bv
                    sub = f"{'+' if delta >= 0 else ''}{delta:,} so với trước"
                    if av < bv:
                        color = COLORS["danger"]
                        warn = True
                col.markdown(kpi_card(t, f"{av:,}" if isinstance(av, int) else "N/A", sub, color),
                             unsafe_allow_html=True)
            if warn:
                st.error("⚠️ CẢNH BÁO: số dòng mh_all/rank_all GIẢM sau rebuild — kiểm tra lại dữ liệu!")
            else:
                st.success("✅ Rebuild thành công. Chuyển sang bước Push GitHub.")
            st.session_state["rebuild_done"] = True

# =====================================================
# SECTION 3 — PUSH TO GITHUB
# =====================================================

section_header("3️⃣ Push lên GitHub")

if not st.session_state["rebuild_done"]:
    st.markdown('<div class="lock-note">🔒 Hoàn tất bước 2 (Rebuild DB) để mở khóa.</div>', unsafe_allow_html=True)
else:
    rc, out, err = run_git(["status", "--short"])
    st.markdown("##### Git status")
    st.code(out or "(không có thay đổi)")
    if err:
        st.code(err)

    st.info("Sẽ chạy: `git add db/esports.duckdb` → `git commit` → `git push origin main`")
    if st.button("✅ Push lên GitHub", type="primary", use_container_width=True):
        msg = f"Data update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        steps = [
            ("add", ["add", "db/esports.duckdb", "dashboard/app.py", "dashboard/team_app.py"]),
            ("commit", ["commit", "-m", msg]),
            ("push", ["push", "origin", "main"]),
        ]
        all_ok = True
        for name, args in steps:
            rc, out, err = run_git(args)
            with st.expander(f"git {name} — {'✅ OK' if rc == 0 else '⚠️ exit ' + str(rc)}",
                             expanded=(rc != 0)):
                if out:
                    st.code(out)
                if err:
                    st.code(err)
            # `commit` returns non-zero when there's nothing to commit — not fatal
            if rc != 0 and name != "commit":
                all_ok = False
                st.error(f"❌ `git {name}` thất bại (exit {rc}).")
                break
        if all_ok:
            st.success("✅ Đã push lên GitHub. Streamlit Cloud sẽ tự rebuild.")
            st.balloons()

# =====================================================
# SECTION 4 — QUẢN LÝ TEAM ACCESS  (always visible)
# =====================================================

# Load tokens once: parse "token = \"TEAM\"" lines → {team: token}
if "tokens" not in st.session_state:
    tokens = {}
    try:
        with open(TOML_PATH, encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            s = line.strip()
            if "=" in line and not s.startswith("#") and not s.startswith("["):
                token, team = line.split("=", 1)
                tokens[team.strip().strip('"')] = token.strip()
    except Exception as e:
        st.session_state["tokens_load_error"] = str(e)
    # ensure every team has a token so the UI never KeyErrors
    for team in TEAM_ORDER:
        tokens.setdefault(team, gen_token())
    st.session_state["tokens"] = tokens
    st.session_state["tokens_saved"] = False

section_header("4️⃣ Quản lý Team Access")

if st.session_state.get("tokens_load_error"):
    st.info(f"Không đọc được {TOML_PATH} ({st.session_state['tokens_load_error']}). Đã tạo token mặc định cho các team thiếu.")

st.warning("⚠️ Sau khi đổi token, nhấn Lưu → Push. Link cũ sẽ không hoạt động ngay sau khi Streamlit Cloud reload.")

for team in TEAM_ORDER:
    token = st.session_state["tokens"].get(team, "")
    col1, col2, col3, col4 = st.columns([1, 4, 2, 1])
    with col1:
        st.markdown(f"**{team}**")
    with col2:
        st.code(f"{TEAM_APP_URL}/?token={token}")
    with col3:
        masked = f"{token[:3]}...{token[-3:]}" if len(token) >= 6 else token
        st.markdown(f"<span style='font-size:11px; color:#8888aa;'>{masked}</span>",
                    unsafe_allow_html=True)
    with col4:
        if st.button("🔄", key=f"gen_{team}"):
            st.session_state["tokens"][team] = gen_token()
            st.session_state["tokens_saved"] = False
            st.rerun()

st.markdown("")
if st.button("💾 Lưu tất cả vào team_tokens.toml", type="primary", use_container_width=True):
    lines = ["[tokens]\n"]
    for team in TEAM_ORDER:
        token = st.session_state["tokens"][team]
        lines.append(f'{token} = "{team}"\n')
    try:
        with open(TOML_PATH, "w", encoding="utf-8") as f:
            f.writelines(lines)
        st.session_state["tokens_saved"] = True
        st.success("✅ Đã lưu. Nhấn Push để áp dụng lên Streamlit Cloud.")
    except Exception as e:
        st.error(f"❌ Không lưu được: {e}")

if not st.session_state["tokens_saved"]:
    st.info("Lưu trước khi push")

if st.button("🚀 Push token lên GitHub", use_container_width=True,
             disabled=not st.session_state["tokens_saved"]):
    steps = [
        ("add", ["add", ".streamlit/team_tokens.toml"]),
        ("commit", ["commit", "-m", f"Update team tokens {datetime.now().strftime('%Y-%m-%d %H:%M')}"]),
        ("push", ["push", "origin", "main"]),
    ]
    all_ok = True
    for name, args in steps:
        rc, out, err = run_git(args)
        with st.expander(f"git {name} — {'✅ OK' if rc == 0 else '⚠️ exit ' + str(rc)}",
                         expanded=(rc != 0)):
            if out:
                st.code(out)
            if err:
                st.code(err)
        # `commit` returns non-zero when there's nothing to commit — not fatal
        if rc != 0 and name != "commit":
            all_ok = False
            st.error(f"❌ `git {name}` thất bại (exit {rc}).")
            break
    if all_ok:
        st.success("✅ Đã push. Streamlit Cloud reload trong ~1 phút. Gửi link mới cho team managers.")
        st.balloons()
        formatted_links = ""
        for team in TEAM_ORDER:
            token = st.session_state["tokens"][team]
            formatted_links += f"{team}: {TEAM_APP_URL}/?token={token}\n"
        st.code(formatted_links)
