from pydantic import BaseModel


class Location(BaseModel):
    id: int
    name: str


class LocationPokemon(BaseModel):
    id: int
    name: str
    types: list[str]