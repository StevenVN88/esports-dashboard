# 🎮 HƯỚNG DẪN SỬ DỤNG ESPORTS ANALYTICS SYSTEM

---

## 📌 CÁC ĐƯỜNG LINK QUAN TRỌNG

| Tên | Link |
|-----|------|
| Admin Dashboard | https://aovesports.streamlit.app |
| Team App | https://aovteam.streamlit.app/?token=XXX |
| GitHub Repo | https://github.com/StevenVN88/esports-dashboard |

---

## 🛠️ ADMIN PANEL (dashboard/admin.py)

Chạy local bằng lệnh:
```
cd D:\EsportsAI\dashboard
python -m streamlit run admin.py
```
Mật khẩu: `esports2024`

---

### SECTION 1 — Upload & Merge CSV

Dùng khi có data mới tải về từ game.

**Bước 1:** Upload file CSV mới vào Section 1
- Có thể upload nhiều file cùng lúc
- File CSV mới chỉ cần chứa DATA MỚI (không cần toàn bộ)
- Hệ thống tự merge với data cũ và xóa duplicate

**Các file được hỗ trợ:**
| File | Duplicate Key |
|------|---------------|
| match_history_vn/th/tw.csv | BattleID + TencentID |
| rank_before_after_raw_vn/th/tw.csv | BattleID + TencentID + Date_Time |
| behavior_info_vnnew/thnew/twnew.csv | BattleID + ReportedOpenID + Date_Time |
| uid_all.csv | TencentID |
| hero.csv | HeroID |

**Bước 2:** Xem preview 5 dòng đầu → kiểm tra đúng file chưa

**Bước 3:** Bấm **✅ Xác nhận Merge**
- Hệ thống tự backup file cũ ({filename}_backup_YYYYMMDD.csv)
- Merge data mới vào, xóa duplicate (giữ row mới nhất)
- Hiển thị stats: rows cũ / mới / trùng bị xóa / kết quả

---

### SECTION 2 — Rebuild Database

⚠️ **Đóng tab aovesports.streamlit.app trước khi rebuild để tránh khóa DB.**

**Bước 1:** Bấm **✅ Xác nhận Rebuild DB**
- Hệ thống chạy toàn bộ pipeline:
  1. build_db.py — Rebuild database từ CSV
  2. build_views.py — Tạo base views
  3. 01_core_views.py — Tạo core views
  4. 02_reporting_views.py — Tạo reporting views
- Hiển thị progress bar và log từng bước
- Hiển thị row counts trước/sau rebuild

⚠️ Nếu số rows mh_all hoặc rank_all bị GIẢM → kiểm tra lại data ngay!

---

### SECTION 3 — Push lên GitHub

**Bước 1:** Kiểm tra git status

**Bước 2:** Bấm **✅ Push lên GitHub**
- Tự động: git add → git commit → git push
- Streamlit Cloud tự detect và rebuild sau ~1-2 phút
- Truy cập https://aovesports.streamlit.app để kiểm tra

---

### SECTION 4 — Quản lý Team Access

Dùng để xem và đổi link truy cập cho 8 team.

**Xem link:** Mỗi team có 1 link riêng dạng:
```
https://aovteam.streamlit.app/?token=XXX
```

**Đổi token cho team:**
1. Bấm **🔄** ở cột cuối của team muốn đổi
2. Token mới được tạo tự động (11 ký tự)
3. Bấm **💾 Lưu tất cả vào team_tokens.toml**
4. Bấm **🚀 Push token lên GitHub**
5. Chờ ~1 phút → link mới hoạt động, link cũ chết

⚠️ Sau khi push xong, gửi link mới cho team manager ngay!

---

## 🔗 LINK TRUY CẬP 8 TEAM

| Team | Link |
|------|------|
| BOX | https://aovteam.streamlit.app/?token=bx7Kf9mQ2vL |
| FPT | https://aovteam.streamlit.app/?token=fT5aHc1dN4x |
| SGP | https://aovteam.streamlit.app/?token=gR9eUi6wB2k |
| SPN | https://aovteam.streamlit.app/?token=qZ4oMl3pX8s |
| FPL | https://aovteam.streamlit.app/?token=hV7yDj5nC1f |
| 1S | https://aovteam.streamlit.app/?token=tN6xRi4cF3v |
| GAM | https://aovteam.streamlit.app/?token=mK8wPj2nD5q |
| TS | https://aovteam.streamlit.app/?token=vL3xTf9bR7s |

⚠️ Token có thể thay đổi nếu admin đã regenerate. Kiểm tra Section 4 để lấy link mới nhất.

---

## 📁 CẤU TRÚC PROJECT

```
D:\EsportsAI\
├── dashboard/
│   ├── app.py          # Admin dashboard (aovesports.streamlit.app)
│   ├── team_app.py     # Team dashboard (aovteam.streamlit.app)
│   └── admin.py        # Admin panel LOCAL (upload data, quản lý token)
├── db/
│   └── esports.duckdb  # Database chính
├── data/               # CSV files
│   └── new/            # Thư mục staging (dùng với UPDATE_DATA.bat)
├── scripts/
│   ├── build_db.py
│   ├── build_views.py
│   ├── 01_core_views.py
│   ├── 02_reporting_views.py
│   └── merge_csv.py
├── .streamlit/
│   └── team_tokens.toml  # Token truy cập 8 team
├── UPDATE_DATA.bat       # Pipeline cũ (dùng CMD thay admin.py)
└── FINAL_SYSTEM_SPEC.md  # Tài liệu kiến trúc hệ thống
```

---

## ⚡ QUICK REFERENCE

**Có data mới:**
→ Mở admin.py → Section 1 Upload → Section 2 Rebuild → Section 3 Push

**Đổi link team:**
→ Mở admin.py → Section 4 → 🔄 Generate → 💾 Lưu → 🚀 Push

**Xem dashboard:**
→ https://aovesports.streamlit.app (admin)
→ https://aovteam.streamlit.app/?token=XXX (team)

---

*Cập nhật lần cuối: 2026-05-29*
