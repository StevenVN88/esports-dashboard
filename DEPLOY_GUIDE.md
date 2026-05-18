# HƯỚNG DẪN DEPLOY LÊN STREAMLIT COMMUNITY CLOUD (FREE)

## 1. Chuẩn bị GitHub Repository

### Bước 1: Tạo repo trên GitHub
- Vào https://github.com → New Repository
- Tên: `esports-dashboard` (hoặc tùy chọn)
- **Private** (để không ai thấy code)

### Bước 2: Cấu trúc folder cần push

```
esports-dashboard/
├── dashboard/
│   ├── app.py            ← Admin dashboard (xem tất cả teams)
│   └── team_app.py       ← Team dashboard (mỗi team 1 link)
├── db/
│   └── esports.duckdb    ← Database file
├── requirements.txt      ← Dependencies
└── .streamlit/
    └── config.toml       ← Theme config
```

### Bước 3: Tạo requirements.txt

```
streamlit
duckdb
plotly
pandas
```

### Bước 4: Tạo .streamlit/config.toml

```toml
[theme]
primaryColor = "#6c5ce7"
backgroundColor = "#0e0e1a"
secondaryBackgroundColor = "#1a1a2e"
textColor = "#e0e0ff"
font = "sans serif"

[server]
headless = true
```

### Bước 5: Push lên GitHub

```bash
cd D:\EsportsAI
git init
git add dashboard/ db/esports.duckdb requirements.txt .streamlit/
git commit -m "Initial deploy"
git remote add origin https://github.com/YOUR_USERNAME/esports-dashboard.git
git push -u origin main
```

⚠️ LƯU Ý: file `esports.duckdb` có thể lớn. Nếu > 100MB thì cần dùng Git LFS.

---

## 2. Deploy lên Streamlit Community Cloud

### Bước 1: Đăng ký
- Vào https://share.streamlit.io
- Đăng nhập bằng GitHub account

### Bước 2: Deploy Admin Dashboard
- Click "New app"
- Chọn repo: `esports-dashboard`
- Branch: `main`
- Main file path: `dashboard/app.py`
- Click "Deploy"

→ URL: `https://esports-dashboard.streamlit.app/`

### Bước 3: Deploy Team Dashboard
- Click "New app" lần nữa
- Chọn repo: `esports-dashboard`
- Branch: `main`
- Main file path: `dashboard/team_app.py`
- Click "Deploy"

→ URL: `https://esports-team.streamlit.app/`

---

## 3. Tạo link riêng cho mỗi Team

Team Dashboard dùng **token bí mật** thay vì team name:

| Team | Link |
|------|------|
| BOX  | `https://esports-team.streamlit.app/?token=bx7Kf9mQ2vL` |
| BSS  | `https://esports-team.streamlit.app/?token=sP3nWj8rY6t` |
| FPT  | `https://esports-team.streamlit.app/?token=fT5aHc1dN4x` |
| SGP  | `https://esports-team.streamlit.app/?token=gR9eUi6wB2k` |
| SPN  | `https://esports-team.streamlit.app/?token=qZ4oMl3pX8s` |
| FPL  | `https://esports-team.streamlit.app/?token=hV7yDj5nC1f` |
| TDT  | `https://esports-team.streamlit.app/?token=wE2uKg8mA9b` |
| 1S   | `https://esports-team.streamlit.app/?token=tN6xRi4cF3v` |

Token mapping nằm trong `.streamlit/team_tokens.toml`.
Đổi token bất cứ lúc nào để revoke access.
Sửa URL không giúp gì — sai token = không vào được.

---

## 4. Phân quyền truy cập

### Admin Dashboard (app.py)
- Settings → Sharing → "This app is viewable by specific viewers"
- Thêm email của bạn (admin)

### Team Dashboard (team_app.py)
- Có thể để public (vì mỗi team chỉ thấy data của họ)
- Hoặc set private + thêm email team owners

---

## 5. Cập nhật data

Khi có data mới:

```bash
# Local: rebuild DB
python scripts/build_db.py
python scripts/build_views.py
python scripts/01_core_views.py
python scripts/02_reporting_views.py

# Push DB mới lên GitHub
git add db/esports.duckdb
git commit -m "Update data"
git push

# Streamlit Cloud tự động reboot app
```

---

## 6. DB Path

⚠️ QUAN TRỌNG: Trên Streamlit Cloud, path là relative từ repo root.

- `app.py` đang dùng: `DB_PATH = r"D:\EsportsAI\db\esports.duckdb"` (local Windows)
- Trên cloud cần đổi thành: `DB_PATH = "db/esports.duckdb"` (relative)

`team_app.py` đã dùng relative path sẵn.
`app.py` cần sửa DB_PATH trước khi deploy.

Cách tốt nhất — dùng biến môi trường hoặc auto-detect:

```python
import os
if os.path.exists("db/esports.duckdb"):
    DB_PATH = "db/esports.duckdb"
else:
    DB_PATH = r"D:\EsportsAI\db\esports.duckdb"
```

---

## Chi phí: FREE
- Streamlit Community Cloud: $0
- GitHub Private Repo: $0
- Custom domain: không hỗ trợ (dùng *.streamlit.app)
- Giới hạn: 1GB RAM, app sleep sau 7 ngày không dùng (tự wake khi truy cập)
