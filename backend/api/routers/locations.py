from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from api.schemas.location import Location, LocationPokemon
from api.services import location_service

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get(
    "",
    response_model=list[Location],
    summary="지도에서 선택할 장소 목록 조회",
    description=(
        "지도에서 선택할 장소의 ID·이름 목록을 조회합니다.\n\n"
        "**사용 방법**\n"
        "- 입력 파라미터는 없습니다.\n"
        "- 반환된 장소 ID로 지도 영역을 선택하거나 출현 포켓몬을 조회합니다."
    ),
    response_description="등록된 장소의 ID·이름 목록",
)
def list_locations():
    return location_service.get_locations()


@router.get(
    "/{location_id}/pokemon",
    response_model=list[LocationPokemon],
    summary="선택한 장소의 출현 포켓몬 조회",
    description=(
        "선택한 장소에 등록된 출현 포켓몬의 ID·이름·타입을 조회합니다.\n\n"
        "**사용 방법**\n"
        "- 장소 목록 API에서 받은 ID를 입력합니다.\n"
        "- 장소는 있지만 등록된 포켓몬이 없으면 `200 OK`와 `[]`를 반환합니다.\n\n"
        "**현재 제공 범위**\n"
        "- 현재 데이터에 등록된 출현 정보만 제공합니다.\n"
        "- 시간·포획 방식·버전별 조건은 구분하지 않습니다."
    ),
    response_description="선택한 장소에 등록된 출현 포켓몬 목록",
    responses={
        404: {"description": "등록된 장소가 없는 ID입니다."},
        422: {"description": "장소 ID를 정수로 해석할 수 없습니다."},
    },
)
def list_location_pokemon(
    location_id: Annotated[int, Path(
        description='**장소 ID (필수)**\n\n- 장소 목록 API에서 받은 ID를 입력합니다.\n- `0`: 리버티가든섬\n- `1`: 1번도로\n\n포켓몬 ID와 별개입니다.',
        examples=[0],
    )],
):
    pokemon = location_service.get_location_pokemon(location_id)
    if pokemon is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 장소입니다.")
    return pokemon
