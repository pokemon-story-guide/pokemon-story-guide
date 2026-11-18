from algorithm.recommendation import _to_rating, evaluate_against_party

INCLUDED_CATEGORIES = {"gym-leader", "elite-four", "champion", "ghetsis"}
CATEGORY_WEIGHTS: dict[str, float] = {}



def _group_key(opponent: dict) -> str:
    if opponent["category"] == "gym-leader" and opponent.get("badge_order") is not None:
        return f"gym-{opponent['badge_order']}"
    return opponent["id"]


def evaluate_overall(my_types: list[str], opponents: list[dict]) -> dict:
    groups: dict[str, dict] = {}
    for opponent in opponents:
        if opponent["category"] not in INCLUDED_CATEGORIES:
            continue
        result = evaluate_against_party(my_types, opponent["party"])
        key = _group_key(opponent)
        group = groups.setdefault(key, {"group": key, "category": opponent["category"], "opponents": []})
        group["opponents"].append({
            "id": opponent["id"],
            "name": opponent.get("name"),
            "score": result["score"],
            "rating": result["rating"],
        })

    if not groups:
        raise ValueError("전체 추천도에 포함할 상대가 없습니다.")

    details = []
    for group in groups.values():
        scores = [item["score"] for item in group["opponents"]]
        group_score = sum(scores) / len(scores)
        details.append({
            **group,
            "score": round(group_score, 1),
            "weight": CATEGORY_WEIGHTS.get(group["category"], 1),
        })

    total_weight = sum(detail["weight"] for detail in details)
    score = round(sum(detail["score"] * detail["weight"] for detail in details) / total_weight)
    rating, rating_label = _to_rating(score)
    ordered = sorted(details, key=lambda detail: detail["score"])

    return {
        "score": score,
        "rating": rating,
        "rating_label": rating_label,
        "summary": {
            "group_count": len(details),
            "good_count": sum(_to_rating(round(d["score"]))[0] == "good" for d in details),
            "bad_count": sum(_to_rating(round(d["score"]))[0] == "bad" for d in details),
            "best_group": ordered[-1]["group"],
            "worst_group": ordered[0]["group"],
        },
        "details": details,
    }