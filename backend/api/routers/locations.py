from fastapi import APIRouter, HTTPException

from api.schemas.location import Location, LocationPokemon
from api.services import location_service

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[Location])
def list_locations():
    return location_service.get_locations()


@router.get("/{location_id}/pokemon", response_model=list[LocationPokemon])
def list_location_pokemon(location_id: int):
    pokemon = location_service.get_location_pokemon(location_id)
    if pokemon is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 장소입니다.")
    return pokemon