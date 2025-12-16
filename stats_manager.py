import json
import datetime
import asyncio
from pathlib import Path
from typing import Union

_stats_lock = asyncio.Lock()
_stats_path_default = Path("data/stats.json")


async def init_stats():
    p = _stats_path_default
    if not p.exists():
        default = {
            "meta": {
                "created_at": datetime.datetime.now().isoformat(),
                "last_updated": None
            },
            "counters": {
                "start": 0,
                "text_messages": 0,
                "start_origin": {}, # { from_origin: count }
                "callbacks": 0,
                "reloads": 0
            },
            "users": {}, # user_id: { "username": username }

            "profiles": {}
            # profile: {
            #     "title": title,
            #     "users": [user_id1, user_id2],
            #     "views": 0
            # }
        }
        await _save(p, default)
    return p

async def _load(p: Path):
    def _read():
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    return await asyncio.to_thread(_read)

async def _save(p: Path, data: dict):
    def _write():
        tmp = p.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(p)
    await asyncio.to_thread(_write)

async def get_stats():
    p = _stats_path_default
    if not p.exists():
        await init_stats()
    return await _load(p)

async def increment_counter(name: str, amount: int = 1):
    p = _stats_path_default
    async with _stats_lock:
        stats = await get_stats()
        stats["counters"].setdefault(name, 0)
        stats["counters"][name] += amount
        stats["meta"]["last_updated"] = datetime.datetime.now().isoformat()
        await _save(p, stats)

async def increment_start(user_id: int, user_tag: str, origin: str):
    p = _stats_path_default
    user_id = str(user_id)
    async with _stats_lock:
        stats = await get_stats()

        # check if user not exists
        users = stats.setdefault("users", {})
        if user_id in users:
            return  # user already counted, do not increment

        print(user_id, user_tag, origin)
        # save user info
        users.setdefault(user_id, {})
        users[user_id]["username"] = user_tag

        # ===================================================
        # ВРЕМЕННО
        await deduplicate_usernames(user_id, user_tag)
        # ВРЕМЕННО
        # ===================================================

        # save and increment origin
        if origin is not None:
            stats["counters"].setdefault("start_origin", {})
            stats["counters"]["start_origin"].setdefault(origin, 0)
            stats["counters"]["start_origin"][origin] += 1
        
        # increment start counter
        stats["counters"].setdefault("start", 0)
        stats["counters"]["start"] += 1
        
        stats["meta"]["last_updated"] = datetime.datetime.now().isoformat()
        await _save(p, stats)

async def increment_profile_view(profile_id: str, profile_title: str, user_id: int):
    p = _stats_path_default
    user_id = str(user_id)
    async with _stats_lock:
        stats = await get_stats()

        # ensure profile exists
        if profile_id not in stats.get("profiles", {}):
            stats.setdefault("profiles", {})
            stats["profiles"].setdefault(profile_id, {})
            stats["profiles"][profile_id]["title"] = profile_title

        # total count
        stats["profiles"][profile_id].setdefault("views", 0)
        stats["profiles"][profile_id]["views"] += 1

        # unique users
        stats["profiles"][profile_id].setdefault("users", [])

        if user_id not in stats["profiles"][profile_id]["users"]:
            stats["profiles"][profile_id]["users"].append(user_id)

        stats["meta"]["last_updated"] = datetime.datetime.now().isoformat()
        await _save(p, stats)

async def collect_user_ids(user_id: int, user_tag: str):
    if user_tag == "no_username":
        return
    p = _stats_path_default
    user_id = str(user_id)
    async with _stats_lock:
        stats = await get_stats()

        users = stats.setdefault("users", {})
        if user_id in users:
            return  # already exists

        old_key = None
        for k, v in users.items():
            if v.get("username") == user_tag:
                old_key = k
                break

        if old_key:
            # переносим данные
            users[user_id] = users.pop(old_key)
        else:
            # вообще новый юзер
            # Вообще такого быть не должно, тк колбек обрабатывается после старта
            print("Случилась фигня: новый юзер в collect_user_ids:", user_id, user_tag)
            users[user_id] = {"username": user_tag}

        stats["meta"]["last_updated"] = datetime.datetime.now().isoformat()

        await _save(p, stats)


async def deduplicate_usernames(user_id: str, user_tag: str, stats: dict):
    p = _stats_path_default
    async with _stats_lock:
        users = stats.setdefault("users", {})

        for k, v in users.items():
            if v.get("username") == user_tag:
                if k != user_id:
                    del users[k]
    await _save(p, stats)