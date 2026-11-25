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


def _get_evolution_relations(pokemon_by_id: dict, family: set[int] | None = None):
    """지정한 계보의 관계를 검증·병합합니다. family가 없으면 전체 데이터를 검증합니다."""
    relations = {}
    for pokemon_id, pokemon in pokemon_by_id.items():
        if family is not None and pokemon_id not in family:
            continue
        for field in ("evolution_from", "evolution_to"):
            entries = pokemon.get(field)
            if entries is None:
                continue
            if not isinstance(entries, list):
                raise ValueError(f"진화 정보는 목록이어야 합니다: {pokemon_id}, {field}")
            for entry in entries:
                if not isinstance(entry, dict):
                    raise ValueError(f"진화 관계가 올바르지 않습니다: {pokemon_id}")
                related_id = entry.get("id")
                if type(related_id) is not int or related_id not in pokemon_by_id:
                    raise ValueError(f"존재하지 않는 진화 포켓몬 ID: {related_id}")
                if related_id == pokemon_id:
                    raise ValueError(f"자기 자신으로 진화할 수 없습니다: {pokemon_id}")
                condition = entry.get("condition")
                if not isinstance(condition, str) or not condition.strip():
                    raise ValueError(f"진화 조건이 올바르지 않습니다: {pokemon_id}")
                condition = f"레벨 {condition}" if condition.isdecimal() else condition
                source, target = (
                    (related_id, pokemon_id) if field == "evolution_from"
                    else (pokemon_id, related_id)
                )
                key = (source, target)
                if key in relations and relations[key]["condition"] != condition:
                    raise ValueError(f"같은 진화 관계의 조건이 다릅니다: {source}, {target}")
                relations[key] = {
                    "from_pokemon_id": source,
                    "to_pokemon_id": target,
                    "condition": condition,
                }
    return list(relations.values())


def _build_evolution_chain(pokemon_id: int, pokemon_by_id: dict):
    # 조건 검증 전에 연결만 찾습니다. 다른 계보의 잘못된 데이터가 조회를 막지 않도록 합니다.
    # 연결된 포켓몬의 잘못된 항목은 계보를 찾은 뒤 아래에서 검증합니다.
    neighbors = {}
    for source, pokemon in pokemon_by_id.items():
        for field in ("evolution_from", "evolution_to"):
            entries = pokemon.get(field)
            if not isinstance(entries, list):
                continue
            for entry in entries:
                target = entry.get("id") if isinstance(entry, dict) else None
                if type(target) is int and target in pokemon_by_id:
                    neighbors.setdefault(source, set()).add(target)
                    neighbors.setdefault(target, set()).add(source)

    # 양방향으로 탐색해 이전 단계와 이후 단계, 같은 계보의 분기를 모두 찾습니다.
    family = set()
    pending = [pokemon_id]
    while pending:
        current = pending.pop()
        if current in family:
            continue
        family.add(current)
        pending.extend(neighbors.get(current, set()) - family)

    relations = _get_evolution_relations(pokemon_by_id, family)
    if not relations:
        pokemon = pokemon_by_id[pokemon_id]
        registered = all(field in pokemon for field in ("evolution_from", "evolution_to"))
        return [] if registered else None

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
    chain = _build_evolution_chain(pokemon_id, pokemon_by_id)
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
