"""관장·사천왕 상대 추천도 계산.

기준값은 모두 아래 '설정값'에 모아 두었습니다. 팀 합의로 기준이 바뀌면 이 부분만 고치면 됩니다.
"""

from algorithm.type_chart import get_multiplier

# ───────────── 설정값 (팀 합의에 따라 수정) ─────────────

# 내가 상대를 공격할 때 배율 → 점수 (내 타입 중 가장 유리한 배율 기준)
OFFENSE_POINTS = {4: 2, 2: 1, 1: 0, 0.5: -1, 0.25: -1, 0: -1}

# 상대가 나를 공격할 때 배율 → 점수 (상대 타입 중 나에게 가장 아픈 배율 기준)
DEFENSE_POINTS = {4: -2, 2: -1, 1: 0, 0.5: 1, 0.25: 1, 0: 2}

# 상대 한 마리당 평균 점수(-4 ~ +4)를 0~100점으로 바꾸는 값
BASE_SCORE = 50
SCORE_PER_POINT = 12.5

# 평가 구간: 위에서부터 차례로 비교해 처음 만족하는 평가를 사용
RATINGS = [
    (65, "good", "좋음"),
    (40, "normal", "보통"),
    (0, "bad", "나쁨"),
]

# ─────────────────────────────────────────────────


def _best_offense(my_types: list[str], opponent_types: list[str]) -> tuple[float, str]:
    """내 타입 중 상대에게 가장 잘 들어가는 배율과 그 타입을 반환합니다."""
    return max((get_multiplier(attack_type, opponent_types), attack_type) for attack_type in my_types)


def _worst_defense(my_types: list[str], opponent_types: list[str]) -> tuple[float, str]:
    """상대 타입 중 나에게 가장 아프게 들어가는 배율과 그 타입을 반환합니다."""
    return max((get_multiplier(attack_type, my_types), attack_type) for attack_type in opponent_types)


def _to_score(average_points: float) -> int:
    score = BASE_SCORE + average_points * SCORE_PER_POINT
    return round(min(100, max(0, score)))


def _to_rating(score: int) -> tuple[str, str]:
    for minimum, rating, label in RATINGS:
        if score >= minimum:
            return rating, label
    return RATINGS[-1][1], RATINGS[-1][2]


def evaluate_against_party(my_types: list[str], opponent_party: list[dict]) -> dict:
    """포켓몬 하나가 상대 파티와 싸울 때의 추천도를 계산합니다.

    my_types: 평가할 포켓몬의 타입 1~2개 (예: ["water", "ground"])
    opponent_party: 상대 포켓몬 목록. 각 항목에 "types"가 꼭 있어야 하고,
        "pokemon_id", "name", "level"이 있으면 근거에 그대로 담깁니다.
    """
    if not opponent_party:
        raise ValueError("상대 파티가 비어 있습니다.")

    details = []
    for opponent in opponent_party:
        offense, attack_type = _best_offense(my_types, opponent["types"])
        defense, threat_type = _worst_defense(my_types, opponent["types"])
        points = OFFENSE_POINTS[offense] + DEFENSE_POINTS[defense]
        details.append({
            "pokemon_id": opponent.get("pokemon_id"),
            "name": opponent.get("name"),
            "level": opponent.get("level"),
            "types": list(opponent["types"]),
            "offense_multiplier": offense,
            "best_attack_type": attack_type,
            "defense_multiplier": defense,
            "threat_type": threat_type,
            "points": points,
        })

    average_points = sum(detail["points"] for detail in details) / len(details)
    score = _to_score(average_points)
    rating, rating_label = _to_rating(score)

    return {
        "score": score,
        "rating": rating,
        "rating_label": rating_label,
        "summary": {
            "opponent_count": len(details),
            "advantage_count": sum(d["offense_multiplier"] > 1 for d in details),
            "disadvantage_count": sum(d["offense_multiplier"] < 1 for d in details),
            "weak_to_count": sum(d["defense_multiplier"] > 1 for d in details),
            "resist_count": sum(d["defense_multiplier"] < 1 for d in details),
            "average_points": round(average_points, 2),
        },
        "details": details,
    }


def rank_candidates(candidates: list[dict], opponent_party: list[dict]) -> list[dict]:
    """관장 상세 화면용: 후보 포켓몬들을 추천 점수가 높은 순으로 정렬합니다.

    candidates: 각 항목에 "types"가 꼭 있어야 하고, "id", "name"은 결과에 그대로 담깁니다.
    점수가 같으면 id가 작은 순서로 정렬합니다.
    """
    ranked = []
    for candidate in candidates:
        result = evaluate_against_party(candidate["types"], opponent_party)
        ranked.append({"id": candidate.get("id"), "name": candidate.get("name"), **result})
    return sorted(ranked, key=lambda item: (-item["score"], item["id"] is None, item["id"] or 0))