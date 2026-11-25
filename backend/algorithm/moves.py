import json
from pathlib import Path

from algorithm.type_chart import get_multiplier

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# 추천 기술 최대 개수
MAX_MOVES = 4

# 자속 보정: 포켓몬과 같은 타입의 기술은 위력 1.5배
STAB_BONUS = 1.5

# 이 값 이하인 기대 위력은 제외 (변화기 0, 위력 변동·조건부 기술 1)
MIN_EXPECTED_POWER = 1

# True면 서로 다른 타입의 기술을 먼저 고르고, 모자라면 같은 타입으로 채움
PREFER_TYPE_COVERAGE = True


_MOVES_BY_ID: dict[int, dict] | None = None
_LEARNSETS: dict[int, list[dict]] | None = None


def _load_data() -> tuple[dict[int, dict], dict[int, list[dict]]]:
    global _MOVES_BY_ID, _LEARNSETS
    if _MOVES_BY_ID is None or _LEARNSETS is None:
        moves = json.loads((DATA_DIR / "move.json").read_text(encoding="utf-8"))
        learn = json.loads((DATA_DIR / "learn.json").read_text(encoding="utf-8"))
        _MOVES_BY_ID = {move["id"]: move for move in moves}
        _LEARNSETS = {entry["pokemon_id"]: entry["moves"] for entry in learn}
    return _MOVES_BY_ID, _LEARNSETS


def get_learnable_moves(pokemon_id: int, level: int | None = None) -> list[dict]:
    moves_by_id, learnsets = _load_data()
    if pokemon_id not in learnsets:
        raise KeyError(f"기술 데이터가 없는 포켓몬입니다: {pokemon_id}")

    first_level: dict[int, int] = {}
    for entry in learnsets[pokemon_id]:
        if level is not None and entry["level"] > level:
            continue
        move_id = entry["move_id"]
        first_level[move_id] = min(entry["level"], first_level.get(move_id, entry["level"]))

    return [
        {**moves_by_id[move_id], "learn_level": learn_level}
        for move_id, learn_level in sorted(first_level.items(), key=lambda item: (item[1], item[0]))
    ]


def _evaluate_move(move: dict, my_types: list[str], opponent_party: list[dict] | None) -> dict:
    stab = STAB_BONUS if move["type"] in my_types else 1
    if opponent_party:
        multipliers = [get_multiplier(move["type"], opponent["types"]) for opponent in opponent_party]
    else:
        multipliers = [1.0]
    average_multiplier = sum(multipliers) / len(multipliers)

    return {
        "id": move["id"],
        "name": move["name"],
        "type": move["type"],
        "expected_power": move["expected_power"],
        "learn_level": move.get("learn_level"),
        "stab": stab > 1,
        "average_multiplier": round(average_multiplier, 2),
        "score": round(move["expected_power"] * stab * average_multiplier, 1),
        "super_effective_count": sum(m > 1 for m in multipliers) if opponent_party else 0,
        "not_very_effective_count": sum(0 < m < 1 for m in multipliers) if opponent_party else 0,
        "no_effect_count": sum(m == 0 for m in multipliers) if opponent_party else 0,
    }


def recommend_moves(
    my_types: list[str],
    learnable_moves: list[dict],
    opponent_party: list[dict] | None = None,
    limit: int = MAX_MOVES,
) -> list[dict]:
    if not my_types:
        raise ValueError("포켓몬 타입이 비어 있습니다.")

    candidates = [
        _evaluate_move(move, my_types, opponent_party)
        for move in learnable_moves
        if move["expected_power"] > MIN_EXPECTED_POWER
    ]
    candidates = [c for c in candidates if c["score"] > 0]
    candidates.sort(key=lambda c: (-c["score"], -c["expected_power"], c["id"]))

    selected: list[dict] = []
    if PREFER_TYPE_COVERAGE:
        used_types: set[str] = set()
        for candidate in candidates:
            if len(selected) == limit:
                break
            if candidate["type"] not in used_types:
                selected.append(candidate)
                used_types.add(candidate["type"])

    for candidate in candidates:
        if len(selected) == limit:
            break
        if candidate not in selected:
            selected.append(candidate)

    return sorted(selected, key=lambda c: (-c["score"], c["id"]))