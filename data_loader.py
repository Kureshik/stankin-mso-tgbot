import json
from pathlib import Path

def load_data(path: str):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"{path} not found")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)
