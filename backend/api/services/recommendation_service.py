"""포켓몬 한 마리와 선택한 상대 파티의 평가·설명을 구성합니다."""

from fastapi import HTTPException

from algorithm.recommendation import evaluate_against_party
from algorithm.type_chart import TYPES
from api.services import pokemon_service, trainer_service
from api.services.recommendation_explanation import EVALUATION_BASIS, build_explanation


def _validate_pokemon(pokemon: dict) -> None:
    types = pokemon["types"]
    if (
        not isinstance(types, list)
        or not 1 <= len(types) <= 2
        or any(not isinstance(value, str) or value not in TYPES for value in types)
        or len(set(types)) != len(types)
    ):
        raise ValueError("포켓몬 타입 데이터가 올바르지 않습니다.")
    if not isinstance(pokemon["name"], str) or not pokemon["name"].strip():
        raise ValueError("포켓몬 이름 데이터가 올바르지 않습니다.")


def get_recommendation(pokemon_id: int, trainer_id: str) -> dict:
    pokemon_by_id = {row["id"]: row for row in pokemon_service.search_pokemon()}
    pokemon = pokemon_by_id.get(pokemon_id)
    if pokemon is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 포켓몬입니다.")
    trainer = trainer_service.get_trainer(trainer_id)
    if trainer is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 인물입니다.")

    _validate_pokemon(pokemon)
    party = []
    for member in trainer["party"]:
        # 이름·타입이 추가된 인물 API와도 호환되도록 포켓몬 ID를 기준으로 조회합니다.
        opponent = pokemon_by_id[member["pokemon_id"]]
        _validate_pokemon(opponent)
        party.append({**member, "name": opponent["name"], "types": opponent["types"]})

    evaluation = evaluate_against_party(pokemon["types"], party)
    return {
        "pokemon_id": pokemon_id,
        "trainer_id": trainer_id,
        "score": evaluation["score"],
        "rating": evaluation["rating"],
        "rating_label": evaluation["rating_label"],
        **build_explanation(evaluation),
        "evaluation_basis": EVALUATION_BASIS,
    }
