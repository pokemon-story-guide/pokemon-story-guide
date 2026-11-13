from typing import Literal
from pydantic import BaseModel

# 관장 목록에서 허용하는 분류 값입니다.
TrainerCategory = Literal["gym-leader", "elite-four", "rival"]

class PartyPokemon(BaseModel):
    pokemon_id: int
    level: int

class TrainerSummary(BaseModel):
    id: str
    name: str
    category: TrainerCategory
    type: str
    badge_order: int | None = None
    image: str

class TrainerDetail(TrainerSummary):
    party: list[PartyPokemon]