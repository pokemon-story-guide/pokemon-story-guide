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
    condition: str = Field(description="실제 데이터에 등록된 진화 조건. 숫자 조건은 레벨로 표시하고 그 외 조건은 원문을 유지합니다.", examples=["레벨 17"])


class PokemonDetail(PokemonCard):
    base_stat_total: int = Field(
        description="포켓몬의 종족값 합계. 개체의 현재 능력치나 레벨을 뜻하지 않습니다.",
        examples=[308],
    )
    # None: 정보 미등록, []: 진화 관계가 없는 것으로 등록됨.
    evolution_chain: list[EvolutionRelation] | None = Field(
        description='mon.json의 이전·이후 관계와 분기를 포함한 전체 진화 계보.\n\n- `null`: 관련 관계를 찾지 못했고 진화 필드가 미등록됨\n- `[]`: 양쪽 진화 필드가 등록되어 있으나 관계가 없음',
    )



class TypeMultiplier(BaseModel):
    type: PokemonType = Field(description="비교 대상인 5세대 영문 타입.", examples=["grass"])
    multiplier: float = Field(ge=0, le=4, description="타입 상성 배율. 0·0.25·0.5·1·2·4 중 하나입니다.", examples=[4])


class DefenseTypeMatchups(BaseModel):
    weak: list[TypeMultiplier] = Field(description="이 타입 공격을 받으면 2배 또는 4배 피해를 받습니다.")
    resist: list[TypeMultiplier] = Field(description="이 타입 공격을 받으면 0.5배 또는 0.25배 피해를 받습니다.")
    immune: list[TypeMultiplier] = Field(description="이 타입 공격은 통하지 않습니다. 배율은 0입니다.")
    neutral: list[TypeMultiplier] = Field(description="이 타입 공격을 받으면 보통 피해를 받습니다. 배율은 1입니다.")


class OffenseTypeMatchups(BaseModel):
    strong: list[TypeMultiplier] = Field(description="포켓몬 자신의 타입으로 공격하면 상대 단일 타입에 2배의 효과가 있습니다.")
    weak: list[TypeMultiplier] = Field(description="포켓몬 자신의 타입 중 유리한 쪽으로 공격해도 상대 단일 타입에 0.5배의 효과입니다.")
    no_effect: list[TypeMultiplier] = Field(description="포켓몬 자신의 모든 타입 공격이 통하지 않는 상대 단일 타입. 배율은 0입니다.")
    neutral: list[TypeMultiplier] = Field(description="포켓몬 자신의 타입 중 유리한 쪽의 배율이 1인 상대 단일 타입.")


class PokemonTypeMatchups(BaseModel):
    pokemon_id: int = Field(ge=0, description="조회한 포켓몬의 하나도감 기준 ID. 전국도감 번호와 다릅니다.", examples=[35])
    types: list[PokemonType] = Field(min_length=1, max_length=2, description="데이터에서 조회한 포켓몬의 타입.", examples=[["ground"]])
    defense: DefenseTypeMatchups = Field(description="포켓몬이 공격받을 때의 타입별 배율. 복합 타입을 반영합니다.")
    offense: OffenseTypeMatchups = Field(description="포켓몬 자신의 타입으로 상대의 단일 타입을 공격한다고 가정한 배율.")
    evaluation_basis: str = Field(description="계산 기준과 실제 기술·특성 등 미반영 정보 안내.")
