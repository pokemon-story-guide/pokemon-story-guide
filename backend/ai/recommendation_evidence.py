"""기존 추천 계산을 바탕으로 타입 상성의 원인을 구성합니다.

모델 호출 없이 포켓몬 JSON과 공통 상성표에서 확인한 사실만 반환합니다.
"""

from fastapi import HTTPException

from algorithm.recommendation import evaluate_against_party
from algorithm.type_chart import get_multiplier
from api.services import pokemon_service, trainer_service
from api.services.recommendation_explanation import EVALUATION_BASIS, TYPE_NAMES
from api.services.recommendation_service import _validate_pokemon

EVIDENCE_BASIS = (
    EVALUATION_BASIS + " 공격은 자신의 타입 중 가장 유리한 타입, "
    "방어는 상대 타입 중 가장 위협적인 타입을 기준으로 합니다. "
    "현재 위치·스토리 진행도에 따른 포획 가능 여부는 반영하지 않습니다. 점수는 승률이 아닙니다."
)


def _type_factors(attack_type: str, defense_types: list[str]) -> list[dict]:
    return [
        {
            "defense_type": defense_type,
            "defense_type_name": TYPE_NAMES[defense_type],
            "multiplier": get_multiplier(attack_type, [defense_type]),
        }
        for defense_type in defense_types
    ]


def _build_direction(
    attacker_name: str,
    defender_name: str,
    attack_type: str,
    defense_types: list[str],
    expected_multiplier: float,
) -> dict:
    factors = _type_factors(attack_type, defense_types)
    multiplier = get_multiplier(attack_type, defense_types)
    if multiplier != expected_multiplier:
        raise ValueError("상성 원인과 기존 추천 계산 결과가 일치하지 않습니다.")

    attack_name = TYPE_NAMES[attack_type]
    factor_text = ", ".join(
        f"{factor['defense_type_name']} 타입에 {factor['multiplier']:g}배"
        for factor in factors
    )
    calculation = " × ".join(f"{factor['multiplier']:g}" for factor in factors)
    reason = f"{attacker_name}의 {attack_name} 타입 공격은 {defender_name}의 {factor_text}로 적용됩니다. "
    if multiplier == 0:
        effect = "immune"
        immune_types = "·".join(
            factor["defense_type_name"] for factor in factors if factor["multiplier"] == 0
        )
        reason += f"{defender_name}의 {immune_types} 타입이 {attack_name} 타입 공격을 무효화하므로 최종 효과는 0배입니다."
    elif multiplier > 1:
        effect = "super_effective"
        reason += f"타입별 배율을 곱하면 최종 {multiplier:g}배로, 타입 상성상 약점을 공략합니다."
    elif multiplier < 1:
        effect = "resisted"
        reason += f"타입별 배율을 곱하면 최종 {multiplier:g}배로, 타입 상성상 공격 효과가 줄어듭니다."
    else:
        effect = "neutral"
        reason += "최종 배율은 1배(등배)로, 이 공격의 타입 상성에 따른 배율 증감은 없습니다."
    return {
        "attacker_name": attacker_name,
        "defender_name": defender_name,
        "attack_type": attack_type,
        "attack_type_name": attack_name,
        "factors": factors,
        "multiplier": multiplier,
        "calculation": f"{calculation} = {multiplier:g}",
        "effect": effect,
        "reason": reason,
    }


def build_recommendation_evidence(pokemon_id: int, trainer_id: str) -> dict:
    """실제 데이터로 AI 입력 근거를 구성합니다. 네트워크 요청은 하지 않습니다."""
    if type(pokemon_id) is not int or pokemon_id < 0:
        raise ValueError("포켓몬 ID는 0 이상의 정수여야 합니다.")
    if not isinstance(trainer_id, str) or not trainer_id or any(c.isspace() for c in trainer_id):
        raise ValueError("트레이너 ID에는 공백을 사용할 수 없습니다.")

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
    trainer = trainer_service.get_trainer(trainer_id)
    if trainer is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 인물입니다.")
    if not isinstance(trainer["name"], str) or not trainer["name"].strip():
        raise ValueError("트레이너 이름 데이터가 올바르지 않습니다.")

    party = []
    for member in trainer["party"]:
        member_id = member["pokemon_id"]
        if type(member_id) is not int:
            raise ValueError("상대 파티의 포켓몬 ID가 올바르지 않습니다.")
        opponent = pokemon_by_id[member_id]
        _validate_pokemon(opponent)
        party.append({**member, "name": opponent["name"], "types": opponent["types"]})

    evaluation = evaluate_against_party(pokemon["types"], party)
    # 같은 포켓몬의 상성은 한 번만 기술하고 실제 파티 내 마릿수를 보존합니다.
    grouped = {}
    for detail in evaluation["details"]:
        opponent_id = detail["pokemon_id"]
        if opponent_id in grouped:
            grouped[opponent_id]["count"] += 1
            continue
        grouped[opponent_id] = {
            "opponent": {
                "pokemon_id": opponent_id,
                "name": detail["name"],
                "types": detail["types"],
                "type_names": [TYPE_NAMES[value] for value in detail["types"]],
            },
            "count": 1,
            "offense": _build_direction(
                pokemon["name"], detail["name"], detail["best_attack_type"],
                detail["types"], detail["offense_multiplier"],
            ),
            "defense": _build_direction(
                detail["name"], pokemon["name"], detail["threat_type"],
                pokemon["types"], detail["defense_multiplier"],
            ),
        }
    return {
        "pokemon": {
            "pokemon_id": pokemon_id,
            "name": pokemon["name"],
            "types": pokemon["types"],
            "type_names": [TYPE_NAMES[value] for value in pokemon["types"]],
        },
        "trainer": {"trainer_id": trainer_id, "name": trainer["name"]},
        "score": evaluation["score"],
        "rating": evaluation["rating"],
        "rating_label": evaluation["rating_label"],
        "evaluation_basis": EVIDENCE_BASIS,
        "matchups": list(grouped.values()),
    }
