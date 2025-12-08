import json
import datetime
import asyncio
from pathlib import Path
from typing import Union

_stats_lock = asyncio.Lock()
_stats_path_default = Path("stats.json")


async def init_stats(path: Union[str, Path] = None):
    p = Path(path) if path else _stats_path_default
    if not p.exists():
        default = {
            "meta": {
                "created_at": datetime.datetime.now().isoformat(),
                "last_updated": None,
            },
            "counters": {
                "start": 0,
                "start_origin": {}, # { from_origin: count }
                "text_messages": 0,
                "callbacks": 0,
                "reloads": 0,
            },
            "profiles": {},        # { profile_id: total_views }
            "profiles_users": {},  # { profile_id: [unique_user_ids] }
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


async def get_stats(path: Union[str, Path] = None):
    p = Path(path) if path else _stats_path_default
    if not p.exists():
        await init_stats(p)
    return await _load(p)


async def increment_counter(name: str, amount: int = 1, path: Union[str, Path] = None):
    p = Path(path) if path else _stats_path_default
    async with _stats_lock:
        stats = await get_stats(p)
        stats["counters"].setdefault(name, 0)
        stats["counters"][name] += amount
        stats["meta"]["last_updated"] = datetime.datetime.now().isoformat()
        await _save(p, stats)

async def increment_start(user_tag: str, origin: str, amount: int = 1, path: Union[str, Path] = None):
    p = Path(path) if path else _stats_path_default
    print(user_tag, origin)
    async with _stats_lock:
        stats = await get_stats(p)

        # check if user not exists
        profiles_users = stats.setdefault("profiles_users", {})
        for _, users in profiles_users.items():
            tag = user_tag or "no_username"
            if tag in users:
                return  # user already counted, do not increment

        if origin is not None:
            stats["counters"].setdefault("start_origin", {})
            stats["counters"]["start_origin"].setdefault(origin, 0)
            stats["counters"]["start_origin"][origin] += amount
        
        stats["counters"].setdefault("start", 0)
        stats["counters"]["start"] += amount
        
        stats["meta"]["last_updated"] = datetime.datetime.now().isoformat()
        await _save(p, stats)


async def increment_profile_view(profile_id: str, user_tag: str, path: Union[str, Path] = None):
    p = Path(path) if path else _stats_path_default

    async with _stats_lock:
        stats = await get_stats(p)

        # total count
        stats.setdefault("profiles", {})
        stats["profiles"].setdefault(profile_id, 0)
        stats["profiles"][profile_id] += 1

        # unique users
        stats.setdefault("profiles_users", {})
        stats["profiles_users"].setdefault(profile_id, [])

        tag = user_tag or "no_username"

        if tag not in stats["profiles_users"][profile_id]:
            stats["profiles_users"][profile_id].append(tag)

        stats["meta"]["last_updated"] = datetime.datetime.now().isoformat()
        await _save(p, stats)
