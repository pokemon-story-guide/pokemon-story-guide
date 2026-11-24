from typing import Literal

from pydantic import BaseModel, Field


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
