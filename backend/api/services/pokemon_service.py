import json
from pathlib import Path
from unicodedata import normalize

from api.services import location_service

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


def _load_pokemon():
    with (DATA_DIR / "mon.json").open(encoding="utf-8") as file:
        return json.load(file)


def search_pokemon(name: str | None = None, pokemon_type: str | None = None):
    """이름 부분 일치와 타입 조건을 모두 만족하는 포켓몬을 반환합니다."""
    keyword = normalize("NFC", name.strip()) if name else ""
    return [
        pokemon
        for pokemon in _load_pokemon()
        if keyword in normalize("NFC", pokemon["name"])
        and (pokemon_type is None or pokemon_type in pokemon["types"])
    ]


def get_pokemon_locations(pokemon_id: int):
    """없는 포켓몬은 None, 등록된 출현 위치가 없으면 빈 목록을 반환합니다."""
    pokemon = next((row for row in _load_pokemon() if row["id"] == pokemon_id), None)
    if pokemon is None:
        return None
    location_ids = pokemon["location_ids"] or []
    if not location_ids:
        return []
    places_by_id = {place["id"]: place for place in location_service.get_locations()}
    # 연결이 잘못된 데이터는 오류로 처리하고 일부 장소만 정상 결과로 반환하지 않습니다.
    return [places_by_id[location_id] for location_id in location_ids]
