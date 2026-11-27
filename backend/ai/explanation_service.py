"""AI가 근거 순서만 선택하고 검증된 문장은 백엔드가 구성합니다."""

import time
from urllib.error import URLError

from ai.ollama_client import DEFAULT_MODEL, request_explanation, validate_explanation_format


def _fact_text(direction: dict, direction_name: str, opponent_name: str, count: int) -> str:
    # 같은 상대가 여러 마리면 문장은 묶되 마릿수는 화면 설명에도 보존합니다.
    opponent_label = f"{opponent_name} {count}마리" if count > 1 else opponent_name
    attacker = direction["attacker_name"]
    defender = direction["defender_name"]
    if direction_name == "defense":
        attacker = opponent_label
    else:
        defender = opponent_label
    attack = direction["attack_type_name"]
    multiplier = direction["multiplier"]
    if multiplier == 0:
        immune_types = "·".join(
            factor["defense_type_name"] for factor in direction["factors"] if factor["multiplier"] == 0
        )
        return f"{defender}의 {immune_types} 타입 때문에 {attacker}의 {attack} 타입 공격은 통하지 않아요."
    factor_text = ", ".join(
        f"{factor['defense_type_name']} 타입에 {factor['multiplier']:g}배"
        for factor in direction["factors"]
    )
    return (
        f"{attacker}의 {attack} 타입 공격은 {defender}의 {factor_text}로 적용돼요. "
        f"최종 효과는 {multiplier:g}배예요."
    )


def build_explanation_catalog(evidence: dict) -> dict:
    """등배를 제외한 모든 공격·방어 이점과 주의점을 필수 근거로 구성합니다."""
    recommendations = []
    warnings = []
    for matchup in evidence["matchups"]:
        for direction_name in ("offense", "defense"):
            direction = matchup[direction_name]
            multiplier = direction["multiplier"]
            if multiplier == 1:
                continue
            is_advantage = (direction_name == "offense" and multiplier > 1) or (
                direction_name == "defense" and multiplier < 1
            )
            category = "recommendation" if is_advantage else "warning"
            fact = {
                "category": category,
                "text": _fact_text(direction, direction_name, matchup["opponent"]["name"], matchup["count"]),
            }
            (recommendations if is_advantage else warnings).append(fact)
    facts = [
        {"id": f"F{index}", **fact}
        for index, fact in enumerate(recommendations + warnings, start=1)
    ]
    return {
        "pokemon": evidence["pokemon"]["name"],
        "trainer": evidence["trainer"]["name"],
        "score": evidence["score"],
        "rating_label": evidence["rating_label"],
        "facts": facts,
    }


def _default_selection(catalog: dict) -> dict:
    return {
        "recommendation_order": [fact["id"] for fact in catalog["facts"] if fact["category"] == "recommendation"],
        "warning_order": [fact["id"] for fact in catalog["facts"] if fact["category"] == "warning"],
    }


def validate_selection(raw_answer: str, catalog: dict) -> dict:
    """분류별 필수 근거가 빠짐없이 한 번씩 선택됐는지 확인합니다."""
    selection = validate_explanation_format(raw_answer)
    expected = _default_selection(catalog)
    for field, expected_ids in expected.items():
        if set(selection[field]) != set(expected_ids):
            raise ValueError("존재하지 않는 근거·잘못된 분류·필수 근거 누락이 있습니다.")
    return selection


def generate_safe_explanation(evidence: dict, *, model: str = DEFAULT_MODEL, timeout: float = 120) -> dict:
    """AI 선택 오류나 호출 실패 시 기본 순서로 설명합니다. 원본 데이터 오류는 숨기지 않습니다."""
    catalog = build_explanation_catalog(evidence)
    selection = _default_selection(catalog)
    result = {
        "score": evidence["score"], "rating": evidence["rating"], "rating_label": evidence["rating_label"],
        "ai_used": False, "used_fallback": False, "fallback_reason": None,
        "ai_error": None, "ai_raw_answer": None, "elapsed_seconds": 0.0,
    }
    if catalog["facts"]:
        started = time.perf_counter()
        try:
            response = request_explanation(catalog, model=model, timeout=timeout)
            result["ai_raw_answer"] = response["raw_answer"]
            selection = validate_selection(response["raw_answer"], catalog)
            result["ai_used"] = True
        except TimeoutError as error:
            result.update(used_fallback=True, fallback_reason="timeout", ai_error=str(error))
        except URLError as error:
            reason = "timeout" if isinstance(error.reason, TimeoutError) else "connection_error"
            result.update(used_fallback=True, fallback_reason=reason, ai_error=str(error))
        except OSError as error:
            result.update(used_fallback=True, fallback_reason="connection_error", ai_error=str(error))
        except ValueError as error:
            result.update(used_fallback=True, fallback_reason="invalid_response", ai_error=str(error))
        result["elapsed_seconds"] = time.perf_counter() - started
    facts_by_id = {fact["id"]: fact["text"] for fact in catalog["facts"]}
    result.update(
        recommendation_reason=" ".join(facts_by_id[value] for value in selection["recommendation_order"])
        or "평가한 타입 상성에서는 뚜렷한 이점이 확인되지 않았어요.",
        warning=" ".join(facts_by_id[value] for value in selection["warning_order"])
        or "평가한 타입 상성에서는 뚜렷한 주의점이 확인되지 않았어요.",
        evaluation_scope=evidence["evaluation_basis"],
        selected_order=selection,
    )
    return result
