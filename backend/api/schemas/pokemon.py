from typing import Literal

from pydantic import BaseModel, Field

PokemonType = Literal[
    "normal", "fire", "water", "electric", "grass", "ice",
    "fighting", "poison", "ground", "flying", "psychic", "bug",
    "rock", "ghost", "dragon", "dark", "steel",
]


class PokemonCard(BaseModel):
    id: int
    name: str
    types: list[PokemonType]
    image: str | None = None


class EvolutionPokemon(BaseModel):
    id: int
    name: str


class EvolutionRelation(BaseModel):
    from_pokemon: EvolutionPokemon = Field(alias="from")
    to: EvolutionPokemon
    condition: str


class PokemonDetail(PokemonCard):
    base_stat_total: int
    # None: 정보 미등록, []: 진화 관계가 없는 것으로 등록됨.
    evolution_chain: list[EvolutionRelation] | None
