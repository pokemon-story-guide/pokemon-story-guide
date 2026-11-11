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


def _load_evolutions():
    """전처리 전에는 별도 목 데이터를 사용합니다. 실제 데이터 연결 시 교체합니다."""
    with (DATA_DIR / "mock" / "evolutions.json").open(encoding="utf-8") as file:
        return json.load(file)


def _build_evolution_chain(pokemon_id: int, pokemon_by_id: dict, evolution_data: dict):
    relations = evolution_data["relations"]
    neighbors = {}
    for relation in relations:
        source = relation["from_pokemon_id"]
        target = relation["to_pokemon_id"]
        neighbors.setdefault(source, set()).add(target)
        neighbors.setdefault(target, set()).add(source)

    if pokemon_id not in neighbors:
        return [] if pokemon_id in evolution_data["no_evolution_pokemon_ids"] else None

    # 양방향으로 탐색해 이전 단계와 이후 단계, 같은 계보의 분기를 모두 찾습니다.
    family = set()
    pending = [pokemon_id]
    while pending:
        current = pending.pop()
        if current in family:
            continue
        family.add(current)
        pending.extend(neighbors[current] - family)

    result = []
    for relation in relations:
        if relation["from_pokemon_id"] not in family:
            continue
        source = pokemon_by_id[relation["from_pokemon_id"]]
        target = pokemon_by_id[relation["to_pokemon_id"]]
        result.append({
            "from": {"id": source["id"], "name": source["name"]},
            "to": {"id": target["id"], "name": target["name"]},
            "condition": relation["condition"],
        })
    return result


def get_pokemon_detail(pokemon_id: int):
    pokemon_by_id = {pokemon["id"]: pokemon for pokemon in _load_pokemon()}
    pokemon = pokemon_by_id.get(pokemon_id)
    if pokemon is None:
        return None
    chain = _build_evolution_chain(pokemon_id, pokemon_by_id, _load_evolutions())
    return {**pokemon, "evolution_chain": chain}
