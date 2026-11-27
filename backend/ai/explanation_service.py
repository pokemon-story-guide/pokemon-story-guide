"""AI가 근거 순서만 선택하고 검증된 문장은 백엔드가 구성합니다."""

import time
from urllib.error import URLError

from ai.ollama_client import DEFAULT_MODEL, request_explanation, validate_explanation_format


def _topic(name: str) -> str:
    """한글 이름의 받침에 맞춰 은/는을 붙입니다."""
    last = ord(name[-1])
    particle = "은" if 0xAC00 <= last <= 0xD7A3 and (last - 0xAC00) % 28 else "는"
    return name + particle


def _fact_text(direction: dict, direction_name: str, opponent_name: str, count: int) -> str:
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
        return f"{_topic(defender)} {immune_types} 타입이라 {attacker}의 {attack} 공격이 통하지 않습니다."
    defense_types = "·".join(factor["defense_type_name"] for factor in direction["factors"])
    return f"{_topic(defender)} {defense_types} 타입이라 {attacker}의 {attack} 공격에 {multiplier:g}배 피해를 받습니다."


def _neutral_facts(evidence: dict) -> list[dict]:
    """같은 방향·타입별 배율인 등배 근거는 상대 이름을 묶어 설명합니다."""
    groups = {}
    for matchup in evidence["matchups"]:
        for direction_name in ("offense", "defense"):
            direction = matchup[direction_name]
            if direction["multiplier"] != 1:
                continue
            key = (
                direction_name, direction["attack_type"],
                tuple((row["defense_type"], row["multiplier"]) for row in direction["factors"]),
            )
            group = groups.setdefault(key, {
                "direction": direction_name, "detail": direction, "opponents": [],
            })
            group["opponents"].append({**matchup["opponent"], "count": matchup["count"]})
    result = []
    pokemon_name = evidence["pokemon"]["name"]
    for group in groups.values():
        detail = group["detail"]
        names = "·".join(
            f"{row['name']} {row['count']}마리" if row["count"] > 1 else row["name"]
            for row in group["opponents"]
        )
        attack_name = detail["attack_type_name"]
        defense_types = "·".join(row["defense_type_name"] for row in detail["factors"])
        if group["direction"] == "offense":
            text = (
                f"{pokemon_name}의 {attack_name} 공격은 "
                f"{defense_types} 타입인 {names}에게 1배입니다."
            )
        else:
            text = (
                f"{names}의 {attack_name} 공격은 {pokemon_name}에게 1배입니다."
            )
        if any(row["multiplier"] != 1 for row in detail["factors"]):
            factor_text = ", ".join(
                f"{row['defense_type_name']} 타입에 {row['multiplier']:g}배"
                for row in detail["factors"]
            )
            text += f" {factor_text}가 곱해져 {detail['calculation']}입니다."
        result.append({
            "direction": group["direction"],
            "attack_type": detail["attack_type"],
            "opponents": group["opponents"],
            "factors": detail["factors"],
            "calculation": detail["calculation"],
            "text": text,
        })
    return result



def _neutral_summary(evidence: dict, neutral_facts: list[dict]) -> str:
    offense = [fact for fact in neutral_facts if fact["direction"] == "offense"]
    defense = [fact for fact in neutral_facts if fact["direction"] == "defense"]
    if len(offense) == len(defense) == 1:
        outgoing, incoming = offense[0], defense[0]
        same_opponents = outgoing["opponents"] == incoming["opponents"]
        all_single_factors_neutral = all(
            factor["multiplier"] == 1
            for fact in (outgoing, incoming) for factor in fact["factors"]
        )
        if same_opponents and all_single_factors_neutral:
            names = "·".join(
                f"{row['name']} {row['count']}마리" if row["count"] > 1 else row["name"]
                for row in outgoing["opponents"]
            )
            # 기존 근거의 타입명을 사용하며 추가 상성 계산은 하지 않습니다.
            from api.services.recommendation_explanation import TYPE_NAMES
            return (
                f"{evidence['pokemon']['name']}의 {TYPE_NAMES[outgoing['attack_type']]} 공격과 "
                f"{names}의 {TYPE_NAMES[incoming['attack_type']]} 공격은 서로 1배입니다. "
                "이번 타입 상성 비교에서는 뚜렷한 유불리가 없습니다."
            )
    return " ".join(fact["text"] for fact in neutral_facts) + " 이번 타입 상성 비교에서는 뚜렷한 유불리가 없습니다."


def build_explanation_catalog(evidence: dict) -> dict:
    """이점·주의점은 AI 선택용 근거로, 등배는 별도 안내용 근거로 구성합니다."""
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
        "neutral_facts": _neutral_facts(evidence),
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


def generate_safe_explanation(evidence: dict, *, model: str = DEFAULT_MODEL, timeout: float = 120, enabled: bool = True) -> dict:
    """AI 선택 오류나 호출 실패 시 기본 순서로 설명합니다. 원본 데이터 오류는 숨기지 않습니다."""
    catalog = build_explanation_catalog(evidence)
    selection = _default_selection(catalog)
    result = {
        "score": evidence["score"], "rating": evidence["rating"], "rating_label": evidence["rating_label"],
        "ai_used": False, "used_fallback": False, "fallback_reason": None,
        "ai_error": None, "ai_raw_answer": None, "elapsed_seconds": 0.0,
        "used_neutral_explanation": not catalog["facts"] and bool(catalog["neutral_facts"]),
        "neutral_explanation": None,
    }
    if catalog["facts"] and not enabled:
        result.update(used_fallback=True, fallback_reason="disabled")
    if catalog["facts"] and enabled:
        started = time.perf_counter()
        try:
            # 등배 자료는 미리보기·기본 안내용이며 기존 AI 입력에는 추가하지 않습니다.
            model_catalog = {key: value for key, value in catalog.items() if key != "neutral_facts"}
            response = request_explanation(model_catalog, model=model, timeout=timeout)
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
    if result["used_neutral_explanation"]:
        result["neutral_explanation"] = _neutral_summary(evidence, catalog["neutral_facts"])
    facts_by_id = {fact["id"]: fact["text"] for fact in catalog["facts"]}
    reasons = [facts_by_id[value] for value in selection["recommendation_order"]]
    warnings = [facts_by_id[value] for value in selection["warning_order"]]
    result.update(
        reasons=reasons,
        warnings=warnings,
        recommendation_reason=" ".join(reasons)
        or "이번 타입 상성 비교에서는 뚜렷한 이점이 없습니다.",
        warning=" ".join(warnings)
        or "이번 타입 상성 비교에서는 뚜렷한 주의점이 없습니다.",
        evaluation_scope=evidence["evaluation_basis"],
        selected_order=selection,
    )
    return result
