from pydantic import BaseModel

class PartyPokemon(BaseModel):
    pokemon_id: int
    level: int

class TrainerSummary(BaseModel):
    id: str
    name: str
    category: str
    type: str
    badge_order: int | None = None
    image: str

class TrainerDetail(TrainerSummary):
    party: list[PartyPokemon]