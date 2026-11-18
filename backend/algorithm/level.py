LEVEL_MARGIN = 0

def get_recommended_level(opponent_party: list[dict]) -> dict:
    """상대 파티의 레벨로 추천 레벨과 산출 근거를 반환합니다.

    opponent_party: 상대 포켓몬 목록. 각 항목에 "level"이 꼭 있어야 합니다.
    승리를 보장하는 레벨이 아니라 공략 참고용 레벨입니다.
    """
    if not opponent_party:
        raise ValueError("상대 파티가 비어 있습니다.")

    levels = [member["level"] for member in opponent_party]
    max_level = max(levels)

    return {
        "recommended_level": max_level + LEVEL_MARGIN,
        "basis": "max_party_level",
        "party_max_level": max_level,
        "party_min_level": min(levels),
        "party_average_level": round(sum(levels) / len(levels), 1),
    }