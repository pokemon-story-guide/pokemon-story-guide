from algorithm.type_chart import TYPES, get_multiplier


def _group_matchups(multipliers, *, above_one: str, below_one: str, zero: str) -> dict:
    result = {above_one: [], below_one: [], zero: [], "neutral": []}
    for type_name, value in multipliers:
        if value == 0:
            group = zero
        elif value > 1:
            group = above_one
        elif value < 1:
            group = below_one
        else:
            group = "neutral"
        result[group].append({"type": type_name, "multiplier": value})
    return result


def get_defense_matchups(defense_types: list[str]) -> dict:
    return _group_matchups(
        ((attack_type, get_multiplier(attack_type, defense_types)) for attack_type in TYPES),
        above_one="weak",
        below_one="resist",
        zero="immune",
    )


def get_offense_matchups(attack_types: list[str]) -> dict:
    if not 1 <= len(attack_types) <= 2:
        raise ValueError("공격 타입은 1개 또는 2개여야 합니다.")

    return _group_matchups(
        (
            (defense_type, max(get_multiplier(attack_type, [defense_type]) for attack_type in attack_types))
            for defense_type in TYPES
        ),
        above_one="strong",
        below_one="weak",
        zero="no_effect",
    )


def get_pokemon_matchups(types: list[str]) -> dict:
    return {
        "types": list(types),
        "defense": get_defense_matchups(types),
        "offense": get_offense_matchups(types),
    }