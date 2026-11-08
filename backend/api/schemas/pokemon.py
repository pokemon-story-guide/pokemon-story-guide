from typing import Literal

from pydantic import BaseModel

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
