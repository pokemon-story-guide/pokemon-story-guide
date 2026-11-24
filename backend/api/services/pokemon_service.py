import json
from pathlib import Path
from unicodedata import normalize

from algorithm.matchup import get_pokemon_matchups
from algorithm.type_chart import TYPES
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



TYPE_MATCHUP_BASIS = (
    "5세대 타입 상성 기준입니다. 방어는 포켓몬의 실제 타입 조합을 사용하며, "
    "공격은 포켓몬 자신의 타입 중 상대 단일 타입에 가장 유리한 배율을 사용합니다. "
    "실제 기술·특성·능력치·레벨은 반영하지 않으며, 공격 평가는 상대의 복합 타입을 반영하지 않습니다."
)


def get_pokemon_type_matchups(pokemon_id: int):
    """ID로 포켓몬 타입을 조회하고 공통 상성 알고리즘의 결과를 반환합니다."""
    pokemon = next((row for row in _load_pokemon() if row["id"] == pokemon_id), None)
    if pokemon is None:
        return None
    types = pokemon["types"]
    if (
        not isinstance(types, list)
        or not 1 <= len(types) <= 2
        or any(not isinstance(value, str) or value not in TYPES for value in types)
        or len(set(types)) != len(types)
    ):
        raise ValueError("포켓몬 타입 데이터가 올바르지 않습니다.")
    return {
        "pokemon_id": pokemon_id,
        **get_pokemon_matchups(types),
        "evaluation_basis": TYPE_MATCHUP_BASIS,
    }
