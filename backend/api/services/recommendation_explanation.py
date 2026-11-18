"""상성 계산 결과에 있는 사실만 사용해 한국어 설명을 만듭니다."""

from collections import Counter

TYPE_NAMES = {
    "normal": "노말", "fire": "불꽃", "water": "물", "electric": "전기",
    "grass": "풀", "ice": "얼음", "fighting": "격투", "poison": "독",
    "ground": "땅", "flying": "비행", "psychic": "에스퍼", "bug": "벌레",
    "rock": "바위", "ghost": "고스트", "dragon": "드래곤", "dark": "악",
    "steel": "강철",
}

EVALUATION_BASIS = (
    "포켓몬 타입에 따른 공격·방어 상성 기준이며, "
    "실제 기술·특성·능력치·레벨은 반영하지 않습니다."
)


def build_explanation(evaluation: dict) -> dict[str, list[str]]:
    """추천 이유와 주의점을 반환합니다. 점수와 평가를 변경하지 않습니다.

    같은 포켓몬의 같은 상성은 한 문장으로 묶고 파티 내 마릿수를 표시합니다.
    방어 배율은 알고리즘이 선택한 '가장 위협적인 상대 타입'의 배율입니다.
    """
    grouped = Counter(
        (
            detail["pokemon_id"], detail["name"],
            detail["best_attack_type"], detail["offense_multiplier"],
            detail["threat_type"], detail["defense_multiplier"],
        )
        for detail in evaluation["details"]
    )
    reasons = []
    warnings = []
    for (_, name, attack_type, offense, threat_type, defense), count in grouped.items():
        opponent = f"{name} {count}마리" if count > 1 else name
        attack = TYPE_NAMES[attack_type]
        threat = TYPE_NAMES[threat_type]

        if offense > 1:
            reasons.append(f"{attack} 타입 공격은 {opponent}에게 {offense:g}배의 효과가 있습니다.")
        elif offense == 0:
            warnings.append(f"{attack} 타입 공격은 {opponent}에게 효과가 없습니다.")
        elif offense < 1:
            warnings.append(f"{attack} 타입 공격은 {opponent}에게 {offense:g}배의 효과만 있습니다.")

        if defense == 0:
            reasons.append(f"{opponent}의 {threat} 타입 공격은 이 포켓몬에게 효과가 없습니다.")
        elif defense < 1:
            reasons.append(f"{opponent}의 {threat} 타입 공격은 이 포켓몬에게 {defense:g}배의 효과만 있습니다.")
        elif defense > 1:
            warnings.append(
                f"{opponent}의 {threat} 타입 공격은 이 포켓몬에게 {defense:g}배의 효과가 있어 주의가 필요합니다."
            )

    if grouped and not reasons and not warnings:
        reasons.append("평가한 공격·방어 배율이 모두 1배로, 타입 상성에 따른 뚜렷한 이점이나 약점이 없습니다.")
    return {"reasons": reasons, "warnings": warnings}
