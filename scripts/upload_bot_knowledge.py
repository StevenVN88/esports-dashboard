"""
upload_bot_knowledge.py
=======================
Auto-upload CSV summary files len Alpha Knowledge Bot (SeaTalk).
Chay sau export_bot_knowledge.py.
"""

import os
import requests

# ══════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════
API_KEY   = "rowZ7KjwvsKiiuvp7bHsm8opya61iQJc"
EXPERT_ID = "8500"
BASE_URL  = "https://knowledge.alpha.insea.io/api"
OUT_DIR   = r"D:\Projects\EsportsAI\reports\bot_knowledge"

HEADERS = {"Authorization": f"Bearer {API_KEY}"}

TARGET_FILES = [
    "00_system_info.txt",
    "01_player_summary.csv",
    "02_team_summary.csv",
    "03_hero_summary.csv",
    "04_rank_current.csv",
    "05_player_hero_pool.csv",
    "06_team_daily_last30.csv",
    "07_player_daily_last30.csv",
]

# ══════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════
def get_existing():
    """GET /experts/{id}/knowledges — lay list knowledge hien co."""
    r = requests.get(f"{BASE_URL}/experts/{EXPERT_ID}/knowledges", headers=HEADERS)
    if r.status_code != 200:
        print(f"  [WARN] Khong lay duoc list: {r.status_code} {r.text[:200]}")
        return {}
    items = r.json().get("knowledges", [])
    return {item["name"]: item["id"] for item in items}


def delete_knowledge(kid):
    r = requests.delete(
        f"{BASE_URL}/experts/{EXPERT_ID}/knowledges/{kid}",
        headers=HEADERS
    )
    return r.status_code in (200, 204)


def upload_file(filepath, folder_id, knowledge_id=None):
    """POST /experts/{id}/knowledges — upload moi hoac update."""
    filename = os.path.basename(filepath)
    mime = "text/csv" if filepath.endswith(".csv") else "text/plain"

    with open(filepath, "rb") as f:
        files = {"file": (filename, f, mime)}
        data  = {"folderId": str(folder_id)}
        if knowledge_id:
            data["knowledgeId"] = str(knowledge_id)

        r = requests.post(
            f"{BASE_URL}/experts/{EXPERT_ID}/knowledges",
            headers=HEADERS,
            files=files,
            data=data
        )

    if r.status_code == 200:
        return True, r.json()
    else:
        return False, r.text


def get_folder_id(folder_name="Folder 1"):
    r = requests.get(f"{BASE_URL}/experts/{EXPERT_ID}/folders", headers=HEADERS)
    if r.status_code != 200:
        print(f"  [WARN] Khong lay duoc folders: {r.status_code}")
        return 0
    folders = r.json().get("folders", [])
    for f in folders:
        if f["name"] == folder_name:
            return f["id"]
    print(f"  [WARN] Khong tim thay '{folder_name}', dung default folder (id=0)")
    return 0


# ══════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════
def main():
    print("\n[Upload] Bat dau upload len Alpha Knowledge Bot...")

    folder_id = get_folder_id("Folder 1")
    print(f"  Folder ID: {folder_id}")

    existing = get_existing()
    print(f"  Hien co {len(existing)} knowledge entries tren bot\n")

    ok_count = 0
    fail_count = 0

    for fname in TARGET_FILES:
        fpath = os.path.join(OUT_DIR, fname)
        if not os.path.exists(fpath):
            print(f"  [SKIP] {fname} - file khong ton tai")
            continue

        old_id = existing.get(fname)
        if old_id:
            ok, result = upload_file(fpath, folder_id, knowledge_id=old_id)
            action = "updated"
        else:
            ok, result = upload_file(fpath, folder_id)
            action = "uploaded"

        if ok:
            print(f"  [OK]   {fname} {action} (id={result.get('id')})")
            ok_count += 1
        else:
            print(f"  [FAIL] {fname}: {str(result)[:300]}")
            fail_count += 1

    print(f"\n  Ket qua: {ok_count} thanh cong, {fail_count} that bai")


if __name__ == "__main__":
    main()
