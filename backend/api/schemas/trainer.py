from typing import Literal

from pydantic import BaseModel, Field

from api.schemas.pokemon import PokemonType

# 관장 목록에서 허용하는 분류 값입니다.
TrainerCategory = Literal["gym-leader", "elite-four", "champion", "plasma"]


class PartyPokemon(BaseModel):
    pokemon_id: int = Field(
        description="하나도감 기준 포켓몬 ID. 전국도감 번호와 다르며, 포켓몬 상세 API의 ID와 같습니다.",
        examples=[93],
    )
    name: str = Field(description="포켓몬의 한글 이름.", examples=["에몽가"])
    types: list[PokemonType] = Field(
        description="5세대 영문 타입 목록. 복합 타입은 두 항목을 반환합니다.",
        examples=[["electric", "flying"]],
    )
    level: int = Field(description="배틀에서 사용하는 레벨.", examples=[25])
    image: str | None = Field(default=None, description="이미지 주소. 현재 데이터에 없으면 null입니다.")


class TrainerSummary(BaseModel):
    id: str = Field(
        description="인물 ID. 상세 조회 주소에 사용합니다.",
        examples=["elesa"],
    )
    name: str = Field(
        description="인물의 한글 이름. N은 이름 뒤에 대전 장소를 함께 표시합니다.",
        examples=["카밀레"],
    )
    category: TrainerCategory = Field(
        description="분류. `gym-leader`: 관장, `elite-four`: 사천왕, `champion`: 챔피언, `plasma`: 플라스마단(게치스·N)",
        examples=["gym-leader"],
    )
    type: str | None = Field(
        description="대표 타입(5세대 영문 타입). 챔피언과 플라스마단은 대표 타입이 없어 빈 문자열입니다.",
        examples=["electric"],
    )
    badge_order: int | None = Field(
        default=None,
        description="관장의 배지 순서(1~8). 관장이 아니면 `null`입니다.",
        examples=[4],
    )
    image: str = Field(
        description="인물 이미지 주소. 아직 준비되지 않은 경우 비어 있을 수 있습니다.",
    )


class TrainerDetail(TrainerSummary):
    party: list[PartyPokemon] = Field(
        description="배틀에서 사용하는 포켓몬 목록. 데이터에 등록된 순서입니다.",
    )