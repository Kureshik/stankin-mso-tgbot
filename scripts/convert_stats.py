import json
import re
from datetime import datetime


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", "_", s)
    return s


with open("data/stats_old.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# --- users ---
user_map = {}
user_ids = {}
uid_counter = 1

for users in data.get("profiles_users", {}).values():
    for username in users:
        if username not in user_map:
            uid = f"u{uid_counter}"
            uid_counter += 1
            user_map[username] = uid
            user_ids[uid] = {"username": username}

# --- profiles ---
profiles = {}

for title, views in data.get("profiles", {}).items():
    slug = slugify(title)
    profiles[slug] = {
        "title": title,
        "users": [],
        "views": views,
    }

for title, users in data.get("profiles_users", {}).items():
    if not users:
        continue

    slug = slugify(title)
    profiles[slug]["users"] = [user_map[u] for u in users]


# --- assemble ---
result = {
    "meta": {
        "created_at": data["meta"]["created_at"],
        "last_updated": datetime.now().isoformat(),
    },
    "counters": data["counters"],
    "users": user_ids,
    "profiles": profiles,
}

with open("data/output.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
