"""포켓몬 한 마리의 주요 상대 전체에 대한 상성 평가를 구성합니다."""

from fastapi import HTTPException

from algorithm.overall import INCLUDED_CATEGORIES, INCLUDED_IDS, evaluate_overall
from api.services import pokemon_service, trainer_service
from api.services.recommendation_explanation import EVALUATION_BASIS
from api.services.recommendation_service import _validate_pokemon

EVALUATION_SCOPE = (
    EVALUATION_BASIS + " 체육관·사천왕·챔피언·게치스를 포함하고 N은 제외합니다. "
    "같은 체육관의 관장 점수는 먼저 평균 내며, 현재 모든 그룹의 비중은 같습니다. "
    "현재 위치·스토리 진행도에 따른 포획 가능 여부는 반영하지 않습니다. 점수는 승률이 아닙니다."
)


def get_overall_recommendation(pokemon_id: int) -> dict:
    pokemon_by_id = {}
    for row in pokemon_service.search_pokemon():
        row_id = row["id"]
        if type(row_id) is not int or row_id < 0 or row_id in pokemon_by_id:
            raise ValueError("포켓몬 ID가 올바르지 않거나 중복되었습니다.")
        pokemon_by_id[row_id] = row
    pokemon = pokemon_by_id.get(pokemon_id)
    if pokemon is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 포켓몬입니다.")
    _validate_pokemon(pokemon)

    opponents = []
    seen_ids = set()
    for trainer in trainer_service.get_trainers():
        if trainer["category"] not in INCLUDED_CATEGORIES and trainer["id"] not in INCLUDED_IDS:
            continue
        trainer_id = trainer["id"]
        if not isinstance(trainer_id, str) or not trainer_id.strip() or trainer_id in seen_ids:
            raise ValueError("트레이너 ID가 올바르지 않거나 중복되었습니다.")
        seen_ids.add(trainer_id)
        if not isinstance(trainer["name"], str) or not trainer["name"].strip():
            raise ValueError("트레이너 이름 데이터가 올바르지 않습니다.")
        badge = trainer.get("badge_order")
        if trainer["category"] == "gym-leader" and badge is not None:
            if type(badge) is not int or badge < 1:
                raise ValueError("체육관 순서 데이터가 올바르지 않습니다.")
        party = []
        for member in trainer["party"]:
            member_id = member["pokemon_id"]
            if type(member_id) is not int:
                raise ValueError("상대 파티의 포켓몬 ID가 올바르지 않습니다.")
            opponent = pokemon_by_id[member_id]
            _validate_pokemon(opponent)
            party.append({**member, "name": opponent["name"], "types": opponent["types"]})
        opponents.append({**trainer, "party": party})

    evaluation = evaluate_overall(pokemon["types"], opponents)
    trainers_by_id = {trainer["id"]: trainer for trainer in opponents}
    details = []
    rating_labels = {"good": "좋음", "normal": "보통", "bad": "나쁨"}
    for detail in evaluation["details"]:
        first_trainer = trainers_by_id[detail["opponents"][0]["id"]]
        badge = first_trainer.get("badge_order")
        group_name = (
            f"{badge}번째 체육관"
            if detail["category"] == "gym-leader" and badge is not None
            else first_trainer["name"]
        )
        details.append({
            **detail,
            "group_name": group_name,
            "opponents": [
                {**opponent, "rating_label": rating_labels[opponent["rating"]]}
                for opponent in detail["opponents"]
            ],
        })
    groups_by_id = {detail["group"]: detail for detail in details}
    summary = evaluation["summary"]
    best = groups_by_id[summary["best_group"]]
    worst = groups_by_id[summary["worst_group"]]
    explanation = (
        f"주요 상대 {summary['group_count']}개 그룹에 대한 타입 상성 종합 점수는 "
        f"{evaluation['score']}점({evaluation['rating_label']})입니다. "
        f"최고 점수 그룹은 {best['group_name']}({best['score']:g}점), "
        f"최저 점수 그룹은 {worst['group_name']}({worst['score']:g}점)입니다. "
        "상대적인 점수 비교이며, 최고 점수도 유리한 상성이나 승리를 보장하지 않습니다."
    )
    return {
        "pokemon_id": pokemon_id,
        "name": pokemon["name"],
        "types": pokemon["types"],
        "score": evaluation["score"],
        "rating": evaluation["rating"],
        "rating_label": evaluation["rating_label"],
        "summary": summary,
        "explanation": explanation,
        "details": details,
        "evaluation_basis": EVALUATION_SCOPE,
    }
