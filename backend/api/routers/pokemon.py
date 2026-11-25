from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from api.schemas.location import Location
from api.schemas.pokemon import PokemonCard, PokemonDetail, PokemonType, PokemonTypeMatchups
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
        "- `null`: 관련 관계를 찾지 못했고 진화 필드가 미등록됨\n"
        "- `[]`: 양쪽 진화 필드가 등록되어 있으나 관계가 없음\n\n"
        "**현재 데이터**\n"
        "- `mon.json`에 등록된 실제 진화 관계를 사용합니다.\n"
        "- ID `1`·`2`·`3`: 주리비얀 → 샤비 → 샤로다 계보를 확인할 수 있습니다.\n"
        "- ID `35`·`36`: 두더류 → 레벨 31 → 몰드류.\n"
        "- 돌·통신·친밀도 등 레벨 이외의 조건은 원문대로 반환합니다."
    ),
    response_description="포켓몬 기본 정보와 진화 관계 목록",
    responses={
        404: {"description": "등록된 포켓몬이 없는 ID입니다."},
        422: {"description": "포켓몬 ID를 정수로 해석할 수 없습니다."},
        500: {"description": "데이터 읽기 실패, 존재하지 않는 진화 포켓몬 참조 또는 잘못된 진화 조건 등 서버 데이터 오류입니다."},
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



@router.get(
    "/{pokemon_id}/type-matchups",
    response_model=PokemonTypeMatchups,
    summary="포켓몬 타입별 공격·방어 상성 조회",
    description=(
        "포켓몬 ID로 타입을 조회하고 기존 공통 알고리즘으로 상성을 계산합니다.\n\n"
        "**입력**\n"
        "- 하나도감 기준 포켓몬 ID만 입력합니다. 타입을 직접 입력하지 않습니다.\n"
        "- ID `0`(비크티니)도 조회할 수 있습니다.\n\n"
        "**방어 상성 (`defense`)**\n"
        "- `weak`: 2배·4배 약점, `resist`: 0.5배·0.25배 반감\n"
        "- `immune`: 0배 무효, `neutral`: 1배 보통\n\n"
        "**공격 상성 (`offense`)**\n"
        "- `strong`: 유리, `weak`: 불리, `no_effect`: 효과 없음, `neutral`: 보통\n"
        "- 자신의 타입이 두 개이면 상대 단일 타입에 가장 유리한 배율을 사용합니다.\n\n"
        "**계산 범위**\n"
        "- 각 목록의 항목은 `type`과 `multiplier`로 구성됩니다. 해당 타입이 없으면 빈 목록입니다.\n"
        "- 공격·방어 각각 5세대 17종 타입을 한 번씩 분류합니다.\n"
        "- 실제 기술·특성·능력치·레벨은 반영하지 않으며, 공격 평가는 상대의 복합 타입을 반영하지 않습니다."
    ),
    response_description="포켓몬 ID·타입, 타입별 공격·방어 상성과 배율, 계산 기준",
    responses={
        404: {"description": "등록되지 않은 포켓몬 ID입니다."},
        422: {"description": "포켓몬 ID가 음수이거나 정수로 해석할 수 없습니다."},
        500: {"description": "데이터 읽기 실패, 누락·중복·허용되지 않은 타입 등 서버 데이터 오류입니다."},
    },
)
def get_pokemon_type_matchups(
    pokemon_id: Annotated[int, Path(
        ge=0,
        description="하나도감 기준 포켓몬 ID. 예: 35 = 두더류. 타입은 데이터에서 조회합니다.",
        examples=[35],
    )],
):
    try:
        result = pokemon_service.get_pokemon_type_matchups(pokemon_id)
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise HTTPException(status_code=500, detail="타입 상성 계산에 필요한 데이터가 올바르지 않습니다.") from error
    if result is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 포켓몬입니다.")
    return result
