import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[3] / "data"

def load_trainers():
    path = DATA_DIR / "mock" / "trainers.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)