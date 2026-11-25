"""HTTP 요청을 실제 상성 근거와 안전한 설명 구성 기능에 연결합니다."""

from ai.explanation_service import generate_safe_explanation
from ai.recommendation_evidence import build_recommendation_evidence

# 로컬 실험용 기본값(120초)과 별도로 웹 요청의 Ollama 통신 timeout을 지정합니다.
MODEL_REQUEST_TIMEOUT_SECONDS = 10.0
RESPONSE_FIELDS = (
    "score", "rating", "rating_label", "recommendation_reason", "warning",
    "neutral_explanation", "evaluation_scope", "ai_used", "used_fallback", "used_neutral_explanation",
)


def get_explanation(pokemon_id: int, trainer_id: str) -> dict:
    evidence = build_recommendation_evidence(pokemon_id, trainer_id)
    result = generate_safe_explanation(evidence, timeout=MODEL_REQUEST_TIMEOUT_SECONDS)
    # 원문·내부 오류·근거 번호 등 실험용 진단 정보는 HTTP 응답에 포함하지 않습니다.
    return {
        "pokemon_id": pokemon_id,
        "trainer_id": trainer_id,
        **{field: result[field] for field in RESPONSE_FIELDS},
    }
