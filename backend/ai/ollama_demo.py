"""근거 순서를 AI가 선택하고 최종 설명은 백엔드에서 구성하는 로컬 실험입니다.

IntelliJ에서 직접 실행하면 모델을 호출합니다.
--preview-only 옵션은 입력 근거만 출력합니다.
"""

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai.explanation_service import build_explanation_catalog, generate_safe_explanation
from ai.ollama_client import DEFAULT_MODEL
from ai.recommendation_evidence import build_recommendation_evidence


def main():
    parser = argparse.ArgumentParser(description="검증된 근거로 AI 설명 구성 실험")
    parser.add_argument("--pokemon-id", type=int, default=25, help="하나도감 포켓몬 ID (기본 25: 콩둘기)")
    parser.add_argument("--trainer-id", default="lenora", help="상대 트레이너 ID (기본 lenora: 알로에)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="설치된 Ollama 모델 이름")
    parser.add_argument("--timeout", type=float, default=120, help="모델 요청 제한 시간(초)")
    parser.add_argument("--preview-only", action="store_true", help="모델에 보낼 근거 목록만 확인")
    args = parser.parse_args()
    evidence = build_recommendation_evidence(args.pokemon_id, args.trainer_id)
    print("AI 입력 근거 목록:", flush=True)
    catalog = build_explanation_catalog(evidence)
    print(json.dumps(catalog, ensure_ascii=False, indent=2), flush=True)
    if args.preview_only:
        print("미리보기 완료 — 모델 호출 없음")
        return 0
    if catalog.get("facts"):
        print(f"\n{args.model}에 근거 순서 선택 요청 중...", flush=True)
    else:
        print("\n전체 등배 안내 구성 중 — 모델 호출 없음", flush=True)
    result = generate_safe_explanation(evidence, model=args.model, timeout=args.timeout)
    print("\nAI 원문:", result["ai_raw_answer"] or "없음")
    print("AI 순서 선택 사용:", "예" if result["ai_used"] else "아니요")
    print("기본 설명으로 대체:", "예" if result["used_fallback"] else "아니요")
    print("전체 등배 안내 사용:", "예" if result.get("used_neutral_explanation") else "아니요")
    if result["used_fallback"]:
        print("대체 사유:", result["fallback_reason"], result["ai_error"])
    elif not result["ai_used"]:
        print("이점·주의점 근거가 없어 모델 요청 없이 등배 안내를 제공합니다.")
    print(f"소요 시간: {result['elapsed_seconds']:.1f}초")
    print(f"기존 평가: {result['score']}점·{result['rating_label']}")
    if result.get("used_neutral_explanation"):
        print("등배 설명:", result["neutral_explanation"])
    else:
        print("추천 이유:", result["recommendation_reason"])
        print("주의점:", result["warning"])
    print("평가 범위:", result["evaluation_scope"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
