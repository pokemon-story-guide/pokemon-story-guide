from typing import Literal

from pydantic import BaseModel, Field

PokemonType = Literal[
    "normal", "fire", "water", "electric", "grass", "ice",
    "fighting", "poison", "ground", "flying", "psychic", "bug",
    "rock", "ghost", "dragon", "dark", "steel",
]


class PokemonCard(BaseModel):
    id: int = Field(description="데이터의 하나도감 기준 포켓몬 ID. 전국도감 번호와 다릅니다.", examples=[1])
    name: str = Field(description="포켓몬의 한글 이름.", examples=["주리비얀"])
    types: list[PokemonType] = Field(
        description="5세대 영문 타입 목록. 복합 타입은 두 항목을 반환합니다.",
        examples=[["grass"]],
    )
    image: str | None = Field(default=None, description="이미지 주소. 현재 데이터에 없으면 null입니다.")


class EvolutionPokemon(BaseModel):
    id: int = Field(description="데이터의 하나도감 기준 포켓몬 ID. 전국도감 번호와 다릅니다.", examples=[1])
    name: str = Field(description="포켓몬의 한글 이름.", examples=["주리비얀"])


class EvolutionRelation(BaseModel):
    from_pokemon: EvolutionPokemon = Field(alias="from", description="진화 전 포켓몬의 ID·이름.")
    to: EvolutionPokemon = Field(description="진화 후 포켓몬의 ID·이름.")
    condition: str = Field(description="진화 조건. 현재 일부 개발용 목 데이터만 등록되어 있습니다.", examples=["레벨 17"])


class PokemonDetail(PokemonCard):
    base_stat_total: int = Field(
        description="포켓몬의 종족값 합계. 개체의 현재 능력치나 레벨을 뜻하지 않습니다.",
        examples=[308],
    )
    # None: 정보 미등록, []: 진화 관계가 없는 것으로 등록됨.
    evolution_chain: list[EvolutionRelation] | None = Field(
        description='이전·이후 단계와 분기를 포함한 전체 진화 계보.\n\n- `null`: 정보 미등록\n- `[]`: 진화 관계 없음으로 등록\n\n현재 일부 목 데이터만 제공합니다.',
    )
