"""
MERGE CSV MỚI VÀO DATA CŨ
Chạy: python scripts/merge_csv.py

Logic:
- Đọc CSV cũ từ data/
- Đọc CSV mới từ data/new/
- Merge (loại trùng bằng key columns)
- Ghi đè lại data/

Hỗ trợ:
- match_history_*.csv  → key: BattleID + TencentID
- rank_before_after_*.csv → key: BattleID + TencentID + Date_Time
- behavior_info_*.csv → key: BattleID + ReportedOpenID + Date_Time
- uid_all.csv → key: TencentID
- hero.csv → key: HeroID
"""

import pandas as pd
import os
import glob
from datetime import datetime

DATA_DIR = r"D:\EsportsAI\data"
NEW_DIR = os.path.join(DATA_DIR, "new")

if not os.path.exists(NEW_DIR):
    os.makedirs(NEW_DIR)
    print(f"Da tao folder: {NEW_DIR}")
    print("Copy CSV moi vao folder nay roi chay lai script.")
    exit()

# Cau hinh merge: ten file → key columns
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

print("=" * 50)
print("MERGE CSV MOI VAO DATA CU")
print("=" * 50)

new_files = os.listdir(NEW_DIR)
new_csv = [f for f in new_files if f.endswith(".csv")]

if not new_csv:
    print(f"\nKhong co file CSV nao trong {NEW_DIR}")
    print("Copy CSV moi vao folder data/new/ roi chay lai.")
    exit()

print(f"\nTim thay {len(new_csv)} file moi: {', '.join(new_csv)}")

for filename in new_csv:
    new_path = os.path.join(NEW_DIR, filename)
    old_path = os.path.join(DATA_DIR, filename)

    if filename not in MERGE_CONFIG:
        print(f"\n⚠️  {filename}: khong co trong MERGE_CONFIG, copy truc tiep.")
        df_new = pd.read_csv(new_path)
        df_new.to_csv(old_path, index=False)
        continue

    keys = MERGE_CONFIG[filename]

    print(f"\n📄 {filename}")
    print(f"   Key: {keys}")

    # Doc file moi
    df_new = pd.read_csv(new_path)
    print(f"   Moi: {len(df_new)} rows")

    if os.path.exists(old_path):
        # Doc file cu
        df_old = pd.read_csv(old_path)
        print(f"   Cu:  {len(df_old)} rows")

        # Merge: concat + drop duplicates
        df_merged = pd.concat([df_old, df_new], ignore_index=True)
        before = len(df_merged)
        df_merged = df_merged.drop_duplicates(subset=keys, keep="last")
        dupes = before - len(df_merged)

        print(f"   Trung: {dupes} rows bi loai")
        print(f"   Ket qua: {len(df_merged)} rows")
    else:
        df_merged = df_new
        print(f"   Chua co file cu, dung file moi.")

    # Backup file cu
    if os.path.exists(old_path):
        backup_path = old_path.replace(".csv", f"_backup_{datetime.now().strftime('%Y%m%d')}.csv")
        os.rename(old_path, backup_path)
        print(f"   Backup: {os.path.basename(backup_path)}")

    # Ghi file merged
    df_merged.to_csv(old_path, index=False)
    print(f"   ✅ Da ghi: {old_path}")

# Don dep: xoa file trong new/ sau khi merge
print(f"\n🧹 Don dep folder new/...")
for f in new_csv:
    os.remove(os.path.join(NEW_DIR, f))
print("   Da xoa file trong data/new/")

print("\n" + "=" * 50)
print("MERGE HOAN TAT!")
print("Chay UPDATE_DATA.bat de rebuild database.")
print("=" * 50)
