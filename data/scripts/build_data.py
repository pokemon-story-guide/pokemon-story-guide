"""PokeAPI에서 데이터를 내려받습니다.

자동 데이터
    mon.json    포켓몬
    move.json   기술
    learn.json  포켓몬별 레벨업 기술

수동 데이터
    data/encounters.json         - 출현 장소
    data/place.json              - 장소 목록

실행
    python data/scripts/build_data.py                    # data/ 에 덮어쓰기
    python data/scripts/build_data.py --out data/_test  # 테스트용 폴더
"""

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://pokeapi.co/api/v2"
VERSION_GROUP = "black-white"
GENERATION = "generation-v"

# 하나 지방 도감 번호로 수정
UNOVA_FIRST_NATIONAL_ID = 494
UNOVA_LAST_NATIONAL_ID = 649
LAST_GEN5_MOVE_ID = 559

DATA_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = Path(__file__).resolve().parent / ".cache"

# 기대 위력 계산을 직접 수정해야 하는 기술
TWO_TURN_MOVE_IDS = {13, 19, 76, 91, 130, 143, 291, 340, 467, 507, 553, 554}
RECHARGE_MOVE_IDS = {63, 307, 308, 338, 416, 439, 459}
FIXED_EXPECTED_POWER = {
    120: 1, 153: 1,248: 1, 353: 1,264: 1, 138: 1, 173: 1, 252: 1, 389: 1, 387: 1, 284: 1, 323: 1, 167: 51, 295: 70,
}

# PokeAPI 상에서 오류가 있는 기술
MOVE_NAME_OVERRIDES = {280: "깨트리기", 343: "탐내기"}

# PokeAPI past_stats 값이 잘못된 포켓몬의 5세대 종족값
BASE_STATS_OVERRIDES = {
    615: [70, 50, 30, 95, 135, 105],  # 프리지오: past_stats에 공격·방어가 뒤바뀌어 있음
}

# 종족값 리스트 순서: HP, 공격, 방어, 특수공격, 특수방어, 스피드
STAT_ORDER = ["hp", "attack", "defense", "special-attack", "special-defense", "speed"]

# 5세대 이후에 종족값이 바뀐 포켓몬 (5세대 값 - 현재 값). PokeAPI 응답에 past_stats가 없을 때만 사용
STAT_CHANGES = {
    508: {"attack": -10},           # 바랜드
    521: {"attack": -10},           # 켄호로우
    526: {"special-defense": -10},  # 기가이아스
    537: {"attack": -10},           # 두빅굴
    542: {"special-defense": -10},  # 모아머
    545: {"attack": -10},           # 펜드라
    553: {"defense": -10},          # 악비아르
}


# ---------------------------------------------------------------- PokeAPI 호출

def fetch(path: str) -> dict:
    """PokeAPI 응답을 .cache 폴더에 저장해 두고, 다음 실행부터는 캐시를 사용합니다.
    PokeAPI 이용 정책(fair use)에 따라 같은 자료를 반복해서 요청하지 않도록 합니다.
    """
    cache_file = CACHE_DIR / (path.strip("/").replace("/", "_") + ".json")
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    request = urllib.request.Request(
        f"{API}/{path.strip('/')}/",
        headers={"User-Agent": "pokemon-story-guide-data-builder"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))

    CACHE_DIR.mkdir(exist_ok=True)
    cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    time.sleep(0.1)
    return data


def id_from_url(url: str) -> int:
    return int(url.rstrip("/").split("/")[-1])


def korean_name(resource: dict) -> str:
    for entry in resource["names"]:
        if entry["language"]["name"] == "ko":
            return entry["name"]
    return resource["name"]


_version_group_order = {}


def version_group_order(name: str) -> int:
    if name not in _version_group_order:
        _version_group_order[name] = fetch(f"version-group/{name}")["order"]
    return _version_group_order[name]


def generation_number(name: str) -> int:
    roman = name.split("-")[1]
    return ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"].index(roman) + 1


# ---------------------------------------------------------------- 포켓몬

def gen5_types(pokemon: dict) -> list[str]:
    """5세대 당시 타입을 검색"""
    target = generation_number(GENERATION)
    candidates = [
        past for past in pokemon.get("past_types", [])
        if generation_number(past["generation"]["name"]) >= target
    ]
    slots = pokemon["types"]
    if candidates:
        slots = min(candidates, key=lambda past: generation_number(past["generation"]["name"]))["types"]
    return [slot["type"]["name"] for slot in sorted(slots, key=lambda slot: slot["slot"])]


def gen5_base_stats(pokemon: dict, national_id: int) -> list[int]:
    """5세대 당시 종족값을 STAT_ORDER 순서의 리스트로 반환합니다."""
    if national_id in BASE_STATS_OVERRIDES:
        return list(BASE_STATS_OVERRIDES[national_id])
    stats = {row["stat"]["name"]: row["base_stat"] for row in pokemon["stats"]}
    target = generation_number(GENERATION)
    candidates = [
        past for past in pokemon.get("past_stats", [])
        if generation_number(past["generation"]["name"]) >= target
    ]
    if candidates:
        old = min(candidates, key=lambda past: generation_number(past["generation"]["name"]))
        for row in old["stats"]:
            stats[row["stat"]["name"]] = row["base_stat"]
    else:
        for name, delta in STAT_CHANGES.get(national_id, {}).items():
            stats[name] += delta
    return [stats[name] for name in STAT_ORDER]


def evolution_condition(details: list[dict]) -> str:
    """진화 조건을 기존 mon.json 표기('17', '태양의 돌', '통신', '친밀도')로 바꿉니다."""
    for detail in details:
        trigger = detail["trigger"]["name"]
        if trigger == "level-up" and detail.get("min_level"):
            return str(detail["min_level"])
        if trigger == "use-item" and detail.get("item"):
            return korean_name(fetch(f"item/{detail['item']['name']}"))
        if trigger == "trade":
            return "통신"
        if trigger == "level-up" and detail.get("min_happiness"):
            return "친밀도"
    return "기타"


def collect_evolutions(chain_root: dict) -> list[tuple[int, int, str]]:
    """진화 계보 작성"""
    result = []
    pending = [chain_root]
    while pending:
        node = pending.pop()
        source = id_from_url(node["species"]["url"])
        for child in node["evolves_to"]:
            target = id_from_url(child["species"]["url"])
            result.append((source, target, evolution_condition(child["evolution_details"])))
            pending.append(child)
    return result


def build_pokemon(encounters: dict[str, list[int]]):
    national_ids = range(UNOVA_FIRST_NATIONAL_ID, UNOVA_LAST_NATIONAL_ID + 1)
    to_local = {national: national - UNOVA_FIRST_NATIONAL_ID for national in national_ids}

    mons, learnsets, relations, chains_seen = [], [], set(), set()
    for national_id in national_ids:
        local_id = to_local[national_id]
        pokemon = fetch(f"pokemon/{national_id}")
        species = fetch(f"pokemon-species/{national_id}")
        print(f"[포켓몬] {local_id:3d} {korean_name(species)}")

        chain_id = id_from_url(species["evolution_chain"]["url"])
        if chain_id not in chains_seen:
            chains_seen.add(chain_id)
            for source, target, condition in collect_evolutions(fetch(f"evolution-chain/{chain_id}")["chain"]):
                if source in to_local and target in to_local:
                    relations.add((to_local[source], to_local[target], condition))

        base_stats = gen5_base_stats(pokemon, national_id)
        mons.append({
            "id": local_id,
            "name": korean_name(species),
            "types": gen5_types(pokemon),
            "base_stats": base_stats,
            "base_stat_total": sum(base_stats),
            "location_ids": encounters.get(str(local_id)),
            "evolution_from": None,
            "evolution_to": None,
            "usable": 0 if species["is_legendary"] or species["is_mythical"] else 1,
        })

        moves = []
        for entry in pokemon["moves"]:
            move_id = id_from_url(entry["move"]["url"])
            for detail in entry["version_group_details"]:
                if (detail["version_group"]["name"] == VERSION_GROUP
                        and detail["move_learn_method"]["name"] == "level-up"):
                    moves.append({"level": detail["level_learned_at"], "move_id": move_id})
        moves.sort(key=lambda move: (move["level"], move["move_id"]))
        learnsets.append({"pokemon_id": local_id, "moves": moves})

    by_id = {mon["id"]: mon for mon in mons}
    for source, target, condition in sorted(relations):
        by_id[source]["evolution_to"] = (by_id[source]["evolution_to"] or []) + [
            {"id": target, "name": by_id[target]["name"], "condition": condition}]
        by_id[target]["evolution_from"] = (by_id[target]["evolution_from"] or []) + [
            {"id": source, "name": by_id[source]["name"], "condition": condition}]
    return mons, learnsets


# ---------------------------------------------------------------- 기술

def gen5_move_values(move: dict) -> dict:
    """5세대 당시의 기술 정보를 구합니다."""
    values = {
        "power": move["power"],
        "accuracy": move["accuracy"],
        "type": move["type"]["name"],
    }
    base_order = version_group_order(VERSION_GROUP)
    later_changes = sorted(
        (past for past in move.get("past_values", [])
         if version_group_order(past["version_group"]["name"]) > base_order),
        key=lambda past: version_group_order(past["version_group"]["name"]),
        reverse=True,
    )
    for past in later_changes:
        for key in ("power", "accuracy"):
            if past.get(key) is not None:
                values[key] = past[key]
        if past.get("type"):
            values["type"] = past["type"]["name"]
    return values


def expected_power(move: dict, values: dict) -> int:
    """기대 위력 = 위력 × 명중률 × 최소 타격 횟수 (반올림)

    - 변화기: 0
    - 일격필살기, 고정 피해기(지구던지기 등)처럼 위력이 정해지지 않은 기술: 1
    - 모으기·반동으로 2턴이 걸리는 기술(솔라빔, 파괴광선 등): 절반
    - 그 밖의 예외(자폭, 꿈먹기 등)는 FIXED_EXPECTED_POWER에 지정
    """
    if move["id"] in FIXED_EXPECTED_POWER:
        return FIXED_EXPECTED_POWER[move["id"]]
    if move["damage_class"]["name"] == "status":
        return 0
    meta = move.get("meta") or {}
    if (meta.get("category") or {}).get("name") == "ohko" or values["power"] is None:
        return 1
    accuracy = values["accuracy"] if values["accuracy"] is not None else 100
    hits = meta.get("min_hits") or 1
    power = values["power"] * accuracy / 100 * hits
    if move["id"] in TWO_TURN_MOVE_IDS | RECHARGE_MOVE_IDS:
        power /= 2
    return int(power + 0.5)


def build_moves():
    moves = []
    for move_id in range(1, LAST_GEN5_MOVE_ID + 1):
        move = fetch(f"move/{move_id}")
        values = gen5_move_values(move)
        name = MOVE_NAME_OVERRIDES.get(move_id, korean_name(move))
        print(f"[기술] {move_id:3d} {name}")
        moves.append({
            "id": move_id,
            "name": name,
            "type": values["type"],
            "expected_power": expected_power(move, values),
        })
    return moves


# ---------------------------------------------------------------- 실행

def read_manual(file_name: str, key: str) -> dict:
    data = json.loads((DATA_DIR / file_name).read_text(encoding="utf-8"))
    return data[key]


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"저장: {path}")


def main():
    parser = argparse.ArgumentParser(description="PokeAPI에서 블랙/화이트 데이터를 생성합니다.")
    parser.add_argument("--out", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    encounters = read_manual("encounters.json", "encounters")

    mons, learnsets = build_pokemon(encounters)
    moves = build_moves()

    write_json(args.out / "mon.json", mons)
    write_json(args.out / "learn.json", learnsets)
    write_json(args.out / "move.json", moves)


if __name__ == "__main__":
    main()