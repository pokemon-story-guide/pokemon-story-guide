from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from api.schemas.location import Location
from api.schemas.pokemon import PokemonCard, PokemonDetail, PokemonType
from api.services import pokemon_service

router = APIRouter(prefix="/pokemon", tags=["pokemon"])


@router.get(
    "",
    response_model=list[PokemonCard],
    summary="포켓몬 이름·타입 검색",
    description=(
        "포켓몬 선택 화면에서 사용할 카드 목록을 조회합니다.\n\n"
        "**검색 방법**\n"
        "- 이름: 한글 이름의 일부로 검색합니다. 예: `주리`\n"
        "- 타입: 주·보조 타입 모두 검색합니다. 예: `grass`\n"
        "- 이름 + 타입: 두 조건을 모두 만족하는 포켓몬을 찾습니다.\n"
        "- 필터 생략: 전체 목록을 반환합니다.\n\n"
        "**결과**\n"
        "- ID·이름·타입·이미지를 반환합니다.\n"
        "- 검색 결과가 없으면 `200 OK`와 `[]`를 반환합니다."
    ),
    response_description="ID·이름·타입·이미지를 포함한 검색 결과 목록",
    responses={422: {"description": "허용되지 않는 타입을 입력한 경우. 빈 타입과 fairy도 허용하지 않습니다."}},
)
def list_pokemon(
    name: str | None = Query(
        default=None,
        description='**이름 검색 (선택)**\n\n- 예: `주리` → 주리비얀\n- 앞뒤 공백은 제거합니다.\n- 생략·빈 문자열·공백만 입력하면 이름 필터를 적용하지 않습니다.',
        examples=["주리"],
    ),
    type: PokemonType | None = Query(
        default=None,
        description='**타입 검색 (선택)**\n\n- 5세대 17종 영문 타입 중 하나를 선택합니다.\n- 주·보조 타입 모두 검색합니다.\n- 이름과 함께 입력하면 두 조건을 모두 적용합니다.\n- 필터를 사용하지 않으면 값을 보내지 마세요. 빈 값·`fairy`는 허용하지 않습니다.',
        examples=["grass"],
    ),
):
    return pokemon_service.search_pokemon(name=name, pokemon_type=type)


@router.get(
    "/{pokemon_id}",
    response_model=PokemonDetail,
    summary="포켓몬 기본 정보·전체 진화 계보 조회",
    description=(
        "선택한 포켓몬의 기본 정보와 전체 진화 계보를 조회합니다.\n\n"
        "**반환 정보**\n"
        "- 기본 정보: ID·이름·타입·이미지·종족값 합계\n"
        "- 진화 계보: 이전·이후 단계와 같은 계보의 분기\n"
        "- 중간·최종 진화체를 선택해도 전체 계보를 반환합니다.\n\n"
        "**진화 정보 읽는 법**\n"
        "- `null`: 진화 정보 미등록\n"
        "- `[]`: 진화 관계가 없는 것으로 등록됨\n\n"
        "**현재 데이터**\n"
        "- 일부 개발용 목 데이터만 연결되어 있습니다.\n"
        "- ID `1`·`2`·`3`: 주리비얀 → 샤비 → 샤로다 계보를 확인할 수 있습니다."
    ),
    response_description="포켓몬 기본 정보와 진화 관계 목록",
    responses={
        404: {"description": "등록된 포켓몬이 없는 ID입니다."},
        422: {"description": "포켓몬 ID를 정수로 해석할 수 없습니다."},
    },
)
def get_pokemon(
    pokemon_id: Annotated[int, Path(
        description='**하나도감 기준 ID (필수)**\n\n- `1`: 주리비얀\n- `2`: 샤비\n- `3`: 샤로다\n\n전국도감 번호와 다릅니다.',
        examples=[1],
    )],
):
    pokemon = pokemon_service.get_pokemon_detail(pokemon_id)
    if pokemon is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 포켓몬입니다.")
    return pokemon


@router.get(
    "/{pokemon_id}/locations",
    response_model=list[Location],
    summary="포켓몬 등장 위치 조회·지도 연결",
    description=(
        "선택한 포켓몬에 등록된 등장 장소를 조회합니다.\n\n"
        "**지도 연결**\n"
        "- 장소의 ID·이름을 원본 데이터 순서대로 반환합니다.\n"
        "- 프론트는 장소 ID를 지도 영역과 연결할 수 있습니다.\n\n"
        "**빈 결과의 의미**\n"
        "- 원본 위치 정보가 `null` 또는 `[]`이면 `200 OK`와 `[]`를 반환합니다.\n"
        "- 등록된 정보가 없다는 뜻이며, 획득 불가를 의미하지 않습니다.\n\n"
        "**입력 예시**\n"
        "- ID `0` = 비크티니 → 현재 리버티가든섬이 등록되어 있습니다."
    ),
    response_description="등록된 등장 장소의 ID·이름 목록",
    responses={
        404: {"description": "등록된 포켓몬이 없는 ID입니다."},
        422: {"description": "포켓몬 ID를 정수로 해석할 수 없습니다."},
        500: {"description": "데이터 읽기 실패 또는 존재하지 않는 장소 ID 참조 등 서버 데이터 오류입니다."},
    },
)
def list_pokemon_locations(
    pokemon_id: Annotated[int, Path(
        description='**하나도감 기준 ID (필수)**\n\n- 예: `0` = 비크티니\n- 전국도감 번호와 다릅니다.',
        examples=[0],
    )],
):
    locations = pokemon_service.get_pokemon_locations(pokemon_id)
    if locations is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 포켓몬입니다.")
    return locations
