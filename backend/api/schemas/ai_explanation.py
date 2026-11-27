from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AiExplanationRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [
            {"pokemon_id": 35, "trainer_id": "elesa"},
            {"pokemon_id": 25, "trainer_id": "lenora"},
        ]},
    )

    pokemon_id: int = Field(
        strict=True, ge=0,
        description="포켓몬 목록에서 받은 하나도감 ID. 전국도감 번호와 다르며, 0(비크티니)도 유효합니다.",
        examples=[35],
    )
    trainer_id: str = Field(
        strict=True, min_length=1, pattern=r"^\S+$",
        description="트레이너 목록에서 받은 ID. 관장·사천왕·챔피언·플라스마 인물을 지원하며 공백은 허용하지 않습니다.",
        examples=["elesa"],
    )

    @field_validator("trainer_id")
    @classmethod
    def reject_whitespace(cls, value: str) -> str:
        if any(char.isspace() for char in value):
            raise ValueError("트레이너 ID에 공백을 사용할 수 없습니다.")
        return value


class AiExplanationResponse(BaseModel):
    pokemon_id: int = Field(ge=0, description="평가한 포켓몬의 하나도감 ID.")
    trainer_id: str = Field(description="평가한 상대 트레이너 ID.")
    score: int = Field(ge=0, le=100, description="기존 알고리즘의 타입 상성 점수. 승률이 아닙니다.")
    rating: Literal["good", "normal", "bad"] = Field(description="기존 평가 코드: 좋음·보통·나쁨.")
    rating_label: Literal["좋음", "보통", "나쁨"] = Field(description="화면에 표시할 평가.")
    recommendation_reason: str = Field(description="검증된 타입 상성 근거로 구성한 추천 이유. 전체 등배에서는 이점이 없다는 안내입니다.")
    warning: str = Field(description="검증된 타입 상성 근거로 구성한 주의점. 해당 사항이 없으면 주의점이 없다는 안내입니다.")
    reasons: list[str] = Field(description="줄별로 표시할 추천 근거 목록. AI 순서 선택 또는 기본 순서를 따르며, 이점이 없으면 빈 목록입니다.")
    warnings: list[str] = Field(description="줄별로 표시할 주의 근거 목록. 해당 사항이 없거나 전체 등배이면 빈 목록입니다.")
    neutral_explanation: str | None = Field(
        default=None,
        description="전체 공격·방어가 등배일 때 상대 이름·공격 타입·1배 근거를 담은 안내. 나머지 경우는 null입니다.",
    )
    evaluation_scope: str = Field(description="타입 상성 기준과 실제 기술·특성·능력치·레벨·포획 가능 여부 등 반영하지 않은 정보.")
    ai_used: bool = Field(description="AI의 근거 순서 선택이 검증을 통과하여 사용됐는지 여부. 문장은 백엔드에서 구성합니다.")
    used_fallback: bool = Field(description="AI 호출 비활성화 또는 모델 응답 오류·연결 실패·시간 초과로 기본 근거 순서를 사용했는지 여부.")
    used_neutral_explanation: bool = Field(description="전체 등배여서 모델 호출 없이 중립 안내를 구성했는지 여부. 이 경우 neutral_explanation을 표시하세요.")
