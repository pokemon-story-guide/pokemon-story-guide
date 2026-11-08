from fastapi import APIRouter, HTTPException, Query

from api.schemas.location import Location
from api.schemas.pokemon import PokemonCard, PokemonType
from api.services import pokemon_service

router = APIRouter(prefix="/pokemon", tags=["pokemon"])


@router.get("", response_model=list[PokemonCard])
def list_pokemon(
    name: str | None = Query(default=None, description="한글 이름 부분 검색. 빈 값은 전체 이름."),
    type: PokemonType | None = Query(default=None, description="5세대 영문 타입명. 이름과 함께 입력하면 AND 검색."),
):
    return pokemon_service.search_pokemon(name=name, pokemon_type=type)


@router.get("/{pokemon_id}/locations", response_model=list[Location])
def list_pokemon_locations(pokemon_id: int):
    locations = pokemon_service.get_pokemon_locations(pokemon_id)
    if locations is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 포켓몬입니다.")
    return locations
