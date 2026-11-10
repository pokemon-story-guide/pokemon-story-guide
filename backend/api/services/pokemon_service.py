import json
from pathlib import Path
from unicodedata import normalize

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
