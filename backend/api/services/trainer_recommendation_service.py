"""선택한 트레이너를 상대할 포켓몬 후보의 순위와 설명을 구성합니다."""

from fastapi import HTTPException

from algorithm.recommendation import rank_candidates
from api.services import pokemon_service, trainer_service
from api.services.recommendation_explanation import EVALUATION_BASIS, build_explanation
from api.services.recommendation_service import _validate_pokemon

EVALUATION_SCOPE = (
    EVALUATION_BASIS + " usable이 1인 포켓몬만 추천 후보로 평가하며, "
    "현재 위치·스토리 진행도에 따른 포획 가능 여부는 반영하지 않습니다. "
    "점수는 승률이 아닙니다."
)


def get_trainer_recommendations(trainer_id: str, limit: int = 10) -> dict:
    trainer = trainer_service.get_trainer(trainer_id)
    if trainer is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 인물입니다.")
    if not isinstance(trainer["name"], str) or not trainer["name"].strip():
        raise ValueError("트레이너 이름 데이터가 올바르지 않습니다.")

    pokemon = pokemon_service.search_pokemon()
    pokemon_by_id = {}
    for candidate in pokemon:
        pokemon_id = candidate["id"]
        if type(pokemon_id) is not int or pokemon_id < 0 or pokemon_id in pokemon_by_id:
            raise ValueError("포켓몬 ID가 올바르지 않거나 중복되었습니다.")
        _validate_pokemon(candidate)
        if type(candidate.get("usable")) is not int or candidate["usable"] not in (0, 1):
            raise ValueError("포켓몬 추천 가능 여부(usable)는 0 또는 1이어야 합니다.")
        pokemon_by_id[pokemon_id] = candidate

    party = []
    for member in trainer["party"]:
        pokemon_id = member["pokemon_id"]
        if type(pokemon_id) is not int:
            raise ValueError("상대 파티의 포켓몬 ID가 올바르지 않습니다.")
        opponent = pokemon_by_id[pokemon_id]
        party.append({**member, "name": opponent["name"], "types": opponent["types"]})
    if not party:
        raise ValueError("상대 파티가 비어 있습니다.")

    # 상대 파티 참조에는 전체 데이터를 사용하고, 추천 후보만 제한합니다.
    candidates = [candidate for candidate in pokemon if candidate["usable"] == 1]
    ranked = rank_candidates(candidates, party)
    return {
        "trainer_id": trainer_id,
        "trainer_name": trainer["name"],
        "total_count": len(ranked),
        "items": [
            {
                "pokemon_id": item["id"],
                "name": item["name"],
                "types": pokemon_by_id[item["id"]]["types"],
                "score": item["score"],
                "rating": item["rating"],
                "rating_label": item["rating_label"],
                **build_explanation(item),
            }
            for item in ranked[:limit]
        ],
        "evaluation_basis": EVALUATION_SCOPE,
    }
