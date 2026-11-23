#상성표는 data/type_chart.json에서 읽음
import json
from pathlib import Path

TYPE_CHART_PATH = Path(__file__).resolve().parents[2] / "data" / "type_chart.json"

TYPES = (
    "normal", "fire", "water", "electric", "grass", "ice",
    "fighting", "poison", "ground", "flying", "psychic", "bug",
    "rock", "ghost", "dragon", "dark", "steel",
)


TYPE_CHART: dict[str, dict[str, float]] = json.loads(TYPE_CHART_PATH.read_text(encoding="utf-8"))


def get_multiplier(attack_type: str, defense_types: list[str]) -> float:
    if attack_type not in TYPE_CHART:
        raise ValueError(f"알 수 없는 공격 타입: {attack_type}")
    if not 1 <= len(defense_types) <= 2:
        raise ValueError("방어 타입은 1개 또는 2개여야 합니다.")

    multiplier = 1.0
    for defense_type in defense_types:
        if defense_type not in TYPES:
            raise ValueError(f"알 수 없는 방어 타입: {defense_type}")
        multiplier *= TYPE_CHART[attack_type].get(defense_type, 1)
    return multiplier