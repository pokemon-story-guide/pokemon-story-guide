from typing import Literal

from pydantic import BaseModel, Field

from api.schemas.pokemon import PokemonType
from api.schemas.trainer import TrainerCategory


class Recommendation(BaseModel):
    pokemon_id: int = Field(description="평가한 포켓몬의 하나도감 ID. 전국도감 번호와 다릅니다.", examples=[35])
    trainer_id: str = Field(description="상대 트레이너 ID.", examples=["elesa"])
    score: int = Field(ge=0, le=100, description="기존 상성 알고리즘이 계산한 0~100점. 승률이 아닙니다.", examples=[54])
    rating: Literal["good", "normal", "bad"] = Field(description="평가 코드. 좋음·보통·나쁨 순서입니다.", examples=["normal"])
    rating_label: Literal["좋음", "보통", "나쁨"] = Field(description="화면에 표시할 평가 문구.", examples=["보통"])
    reasons: list[str] = Field(
        description="공격상 이점·방어상 이점 또는 중립 평가의 설명. 유리한 근거가 없으면 빈 목록일 수 있습니다.",
        examples=[["땅 타입 공격은 제브라이카에게 2배의 효과가 있습니다."]],
    )
    warnings: list[str] = Field(
        description="공격 반감·무효 또는 방어 약점. 해당하는 경우가 없으면 빈 목록입니다.",
        examples=[["땅 타입 공격은 에몽가 2마리에게 효과가 없습니다."]],
    )
    evaluation_basis: str = Field(description="평가에 반영한 정보와 반영하지 않은 정보 안내.")


class TrainerEvaluation(BaseModel):
    trainer_id: str = Field(description="상대 트레이너 ID.", examples=["cilan"])
    trainer_name: str = Field(description="상대 트레이너의 한글 이름.", examples=["덴트"])
    category: TrainerCategory = Field(description="트레이너 분류.", examples=["gym-leader"])
    badge_order: int | None = Field(description="관장의 배지 순서(1~8). 관장이 아니면 `null`입니다.", examples=[1])
    score: int = Field(ge=0, le=100, description="기존 상성 알고리즘이 계산한 0~100점. 승률이 아닙니다.", examples=[46])
    rating: Literal["good", "normal", "bad"] = Field(description="평가 코드. 좋음·보통·나쁨 순서입니다.", examples=["normal"])
    rating_label: Literal["좋음", "보통", "나쁨"] = Field(description="화면에 표시할 평가 문구.", examples=["보통"])
    reasons: list[str] = Field(description="공격·방어상 이점 또는 중립 평가의 설명. 없으면 빈 목록입니다.")
    warnings: list[str] = Field(description="공격 반감·무효 또는 방어 약점. 없으면 빈 목록입니다.")


class PokemonTrainerEvaluations(BaseModel):
    pokemon_id: int = Field(description="평가한 포켓몬의 하나도감 ID.", examples=[16])
    name: str = Field(description="평가한 포켓몬의 한글 이름.", examples=["레파르다스"])
    types: list[PokemonType] = Field(description="평가한 포켓몬의 타입.", examples=[["dark"]])
    items: list[TrainerEvaluation] = Field(
        description="트레이너별 평가. 트레이너 목록 API와 같은 순서(관장 배지 순 → 사천왕 → 챔피언 → 플라스마단)입니다.",
    )
    evaluation_basis: str = Field(description="평가에 반영한 정보와 반영하지 않은 정보 안내.")


class TrainerRecommendationItem(BaseModel):
    pokemon_id: int = Field(ge=0, description="후보 포켓몬의 하나도감 ID. 전국도감 번호와 다릅니다.")
    name: str = Field(description="후보 포켓몬의 한글 이름.")
    types: list[PokemonType] = Field(min_length=1, max_length=2, description="후보 포켓몬의 영문 타입 목록.")
    score: int = Field(ge=0, le=100, description="공격·방어 상성 점수. 승률이 아닙니다.")
    rating: Literal["good", "normal", "bad"] = Field(description="평가 코드: 좋음·보통·나쁨.")
    rating_label: Literal["좋음", "보통", "나쁨"] = Field(description="화면에 표시할 평가 문구.")
    reasons: list[str] = Field(description="이 후보의 공격·방어상 이점. 중립이면 중립 설명을 반환합니다.")
    warnings: list[str] = Field(description="이 후보의 공격 반감·무효 또는 방어 약점. 없으면 빈 목록입니다.")


class TrainerRecommendations(BaseModel):
    trainer_id: str = Field(description="선택한 상대 트레이너 ID.", examples=["elesa"])
    trainer_name: str = Field(description="선택한 상대 트레이너의 한글 이름.", examples=["카밀레"])
    total_count: int = Field(ge=0, description="usable이 1인 후보 수. usable 필터 적용 후, limit 적용 전 개수.")
    items: list[TrainerRecommendationItem] = Field(
        description="usable이 1인 후보의 상성 점수 내림차순 추천 목록. 동점은 포켓몬 ID 오름차순. limit개까지 반환합니다.",
    )
    evaluation_basis: str = Field(description="평가 기준과 포획 가능 여부 등 반영하지 않은 정보 안내.")
