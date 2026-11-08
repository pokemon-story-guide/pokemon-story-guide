import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


def _load_json(file_name: str):
    with (DATA_DIR / file_name).open(encoding="utf-8") as file:
        return json.load(file)


def get_locations():
    return _load_json("place.json")


def get_location_pokemon(location_id: int):
    """장소가 없으면 None, 장소는 있지만 출현 포켓몬이 없으면 빈 목록을 반환합니다."""
    if not any(location["id"] == location_id for location in get_locations()):
        return None

    return [
        pokemon
        for pokemon in _load_json("mon.json")
        if location_id in (pokemon["location_ids"] or [])
    ]