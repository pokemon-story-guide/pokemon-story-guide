"""실제 데이터에서 서로 다른 대표 사례를 골라 AI의 근거 순서 선택을 확인합니다.

기본 실행은 사례 목록만 출력합니다. --run-model을 지정해야 Ollama를 호출합니다.
결과 저장: python -m ai.generalization_demo --run-model --output /private/tmp/ai-generalization.json
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai.explanation_service import build_explanation_catalog, generate_safe_explanation
from ai.ollama_client import DEFAULT_MODEL
from ai.recommendation_evidence import build_recommendation_evidence
from algorithm.recommendation import evaluate_against_party
from api.services import pokemon_service, trainer_service


FEATURE_LABELS = {
    "single_type": "단일 타입",
    "dual_type": "복합 타입",
    "offense_immunity": "내 공격 무효",
    "defense_immunity": "상대 공격 무효",
    "four_times": "4배 상성",
    "quarter_resistance": "¼배 반감",
    "only_advantages": "이점만 있음",
    "only_warnings": "주의점만 있음",
    "neutral": "모든 평가 등배",
    "most_facts": "최대 근거 수",
}


def select_representative_cases(max_cases: int = 8) -> dict:
    """캐시한 원본 자료로 전체를 탐색하고 검증용 사례만 실제 서비스에 연결합니다."""
    if type(max_cases) is not int or max_cases < 1:
        raise ValueError("사례 수는 1 이상의 정수여야 합니다.")
    pokemon = pokemon_service.search_pokemon()
    by_id = {row["id"]: row for row in pokemon}
    trainers = trainer_service.get_trainers()
    candidates = []
    # 모델 실험은 현재 추천 후보인 usable=1 포켓몬으로 우선 구성합니다.
    # 자동 검증은 usable 값과 관계없이 등록된 포켓몬 전체를 대상으로 합니다.
    for row in pokemon:
        if row.get("usable") != 1:
            continue
        for trainer in trainers:
            party = [{**member, "types": by_id[member["pokemon_id"]]["types"]} for member in trainer["party"]]
            evaluation = evaluate_against_party(row["types"], party)
            unique = {detail["pokemon_id"]: detail for detail in evaluation["details"]}.values()
            advantages = 0
            warnings = 0
            features = {"single_type" if len(row["types"]) == 1 else "dual_type"}
            for detail in unique:
                offense, defense = detail["offense_multiplier"], detail["defense_multiplier"]
                advantages += int(offense > 1) + int(defense < 1)
                warnings += int(offense < 1) + int(defense > 1)
                if offense == 0:
                    features.add("offense_immunity")
                if defense == 0:
                    features.add("defense_immunity")
                if 4 in (offense, defense):
                    features.add("four_times")
                if 0.25 in (offense, defense):
                    features.add("quarter_resistance")
            if advantages and not warnings:
                features.add("only_advantages")
            if warnings and not advantages:
                features.add("only_warnings")
            if not advantages and not warnings:
                features.add("neutral")
            candidates.append({
                "pokemon_id": row["id"], "pokemon_name": row["name"],
                "trainer_id": trainer["id"], "trainer_name": trainer["name"],
                "features": features, "fact_count": advantages + warnings,
            })
    if not candidates:
        raise ValueError("대표 사례를 선정할 추천 후보가 없습니다.")
    maximum = max(case["fact_count"] for case in candidates)
    for case in candidates:
        if case["fact_count"] == maximum:
            case["features"].add("most_facts")
    available = set().union(*(case["features"] for case in candidates))
    remaining = set(available)
    selected = []
    while remaining and len(selected) < max_cases:
        case = max(candidates, key=lambda case: (len(case["features"] & remaining), case["fact_count"]))
        if not case["features"] & remaining:
            break
        selected.append({**case, "features": sorted(case["features"])})
        remaining -= case["features"]
    return {
        "dataset": {"pokemon_count": len(pokemon), "trainer_count": len(trainers), "combination_count": len(pokemon) * len(trainers)},
        "model": DEFAULT_MODEL,
        "available_features": sorted(available),
        "unavailable_features": sorted(set(FEATURE_LABELS) - available),
        "uncovered_features": sorted(remaining),
        "cases": selected,
    }


def main():
    parser = argparse.ArgumentParser(description="AI 일반화 대표 사례 확인")
    parser.add_argument("--run-model", action="store_true", help="실제 로컬 모델 요청 허용")
    parser.add_argument("--max-cases", type=int, default=8)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--output", type=Path, help="선택 결과와 실제 실행 결과를 저장할 JSON 경로")
    args = parser.parse_args()
    report = select_representative_cases(args.max_cases)
    report["model"] = args.model
    report["model_calls_enabled"] = args.run_model
    for case in report["cases"]:
        labels = ", ".join(FEATURE_LABELS[value] for value in case["features"])
        print(f"{case['pokemon_name']} vs {case['trainer_name']}: {labels} / 근거 {case['fact_count']}개", flush=True)
        if args.run_model:
            evidence = build_recommendation_evidence(case["pokemon_id"], case["trainer_id"])
            catalog = build_explanation_catalog(evidence)
            result = generate_safe_explanation(evidence, model=args.model, timeout=args.timeout)
            case["result"] = result
            case["all_facts_preserved"] = all(
                fact["text"] in result["recommendation_reason" if fact["category"] == "recommendation" else "warning"]
                for fact in catalog["facts"]
            )
            print(f"  AI 사용={result['ai_used']}, 대체={result['used_fallback']}, {result['elapsed_seconds']:.1f}초, 근거 보존={case['all_facts_preserved']}", flush=True)
    counts = Counter(
        "ai" if case["result"]["ai_used"] else "fallback" if case["result"]["used_fallback"] else "not_needed"
        for case in report["cases"] if "result" in case
    )
    report["result_counts"] = dict(counts)
    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"결과 저장: {args.output}")
    if report["unavailable_features"]:
        print("실제 후보 데이터에 없는 유형:", ", ".join(FEATURE_LABELS[value] for value in report["unavailable_features"]))
    if report["uncovered_features"]:
        print("사례 수 제한으로 확인하지 못한 유형:", report["uncovered_features"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
