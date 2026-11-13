"""포켓몬 타입 기준 상성 정리 (포켓몬 상세 화면용)."""

from algorithm.type_chart import TYPES, get_multiplier


def get_defense_matchups(defense_types: list[str]) -> dict:
    """모든 공격 타입이 이 포켓몬에게 주는 배율을 약점/반감/무효로 나눕니다."""
    result = {"weak": [], "resist": [], "immune": [], "neutral": []}
    for attack_type in TYPES:
        multiplier = get_multiplier(attack_type, defense_types)
        entry = {"type": attack_type, "multiplier": multiplier}
        if multiplier == 0:
            result["immune"].append(entry)
        elif multiplier > 1:
            result["weak"].append(entry)
        elif multiplier < 1:
            result["resist"].append(entry)
        else:
            result["neutral"].append(entry)
    return result


def get_offense_matchups(attack_types: list[str]) -> dict:
    """이 포켓몬의 타입(자속 기술 기준)으로 각 타입을 공격할 때 가장 좋은 배율을 나눕니다."""
    if not 1 <= len(attack_types) <= 2:
        raise ValueError("공격 타입은 1개 또는 2개여야 합니다.")

    result = {"strong": [], "weak": [], "no_effect": [], "neutral": []}
    for defense_type in TYPES:
        multiplier = max(get_multiplier(attack_type, [defense_type]) for attack_type in attack_types)
        entry = {"type": defense_type, "multiplier": multiplier}
        if multiplier == 0:
            result["no_effect"].append(entry)
        elif multiplier > 1:
            result["strong"].append(entry)
        elif multiplier < 1:
            result["weak"].append(entry)
        else:
            result["neutral"].append(entry)
    return result


def get_pokemon_matchups(types: list[str]) -> dict:
    """포켓몬 상세 화면에 보여줄 방어·공격 상성을 한 번에 반환합니다."""
    return {
        "types": list(types),
        "defense": get_defense_matchups(types),
        "offense": get_offense_matchups(types),
    }