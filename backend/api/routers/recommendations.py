from fastapi import APIRouter, HTTPException, Path, Query

from api.schemas.recommendation import PokemonTrainerEvaluations, Recommendation
from api.schemas.trainer import TrainerCategory
from api.services import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get(
    "",
    response_model=Recommendation,
    summary="포켓몬과 상대 트레이너의 상성 평가·이유 조회",
    description=(
        "포켓몬 한 마리가 선택한 트레이너의 파티를 상대할 때의 타입 상성을 평가합니다.\n\n"
        "**사용 방법**\n"
        "- 포켓몬 목록의 `id`와 트레이너 목록의 `id`를 전달합니다.\n"
        "- 예: `pokemon_id=35`, `trainer_id=elesa` → 두더류와 카밀레의 파티 비교\n\n"
        "**반환 정보**\n"
        "- 점수(0~100), 평가(좋음·보통·나쁨), 추천 이유, 주의점\n"
        "- 공격에 유리해도 방어에 약점이 있으면 주의점을 함께 반환합니다.\n"
        "- 동일 포켓몬의 같은 상성은 문장을 묶고 마릿수를 표시합니다.\n\n"
        "**평가 범위**\n"
        "- 점수와 배율은 기존 공통 알고리즘을 사용하고 설명은 규칙에 따라 생성합니다.\n"
        "- 포켓몬 자신의 타입을 공격 타입으로 가정합니다. 실제 보유 기술·특성·능력치·레벨은 반영하지 않습니다.\n"
        "- 점수는 승률이 아니며, 현재 포획 가능 여부나 승리를 보장하지 않습니다.\n"
        "- 후보 목록을 추천하는 API가 아니라, 지정한 포켓몬 한 마리의 상대별 평가 API입니다."
    ),
    response_description="선택한 조합의 상성 점수·평가와 한국어 설명",
    responses={
        404: {"description": "등록되지 않은 포켓몬 또는 트레이너 ID입니다."},
        422: {"description": "필수 ID 누락, 음수·정수가 아닌 포켓몬 ID, 빈 트레이너 ID입니다."},
        500: {"description": "데이터 읽기 실패, 잘못된 포켓몬 참조·타입 또는 빈 상대 파티 등 서버 데이터 오류입니다."},
    },
)
def get_recommendation(
    pokemon_id: int = Query(ge=0, description="하나도감 기준 포켓몬 ID. 0(비크티니)도 유효합니다.", examples=[35]),
    trainer_id: str = Query(min_length=1, pattern=r"^\S+$", description="목록 API에서 받은 트레이너 ID. 공백은 허용하지 않습니다.", examples=["elesa"]),
):
    try:
        return recommendation_service.get_recommendation(pokemon_id, trainer_id)
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise HTTPException(status_code=500, detail="추천 계산에 필요한 데이터가 올바르지 않습니다.") from error


@router.get(
    "/pokemon/{pokemon_id}",
    response_model=PokemonTrainerEvaluations,
    summary="포켓몬 한 마리의 트레이너별 상성 평가·이유 목록 조회",
    description=(
        "선택한 포켓몬 한 마리를 트레이너마다 비교한 평가를 한 번에 반환합니다.\n\n"
        "**사용 방법**\n"
        "- 포켓몬 목록의 `id`를 전달합니다. 예: `/api/recommendations/pokemon/16?category=gym-leader` → 레파르다스의 관장별 평가\n"
        "- `category`를 보내지 않으면 모든 트레이너를 평가합니다.\n\n"
        "**반환 정보**\n"
        "- 트레이너별 점수(0~100), 평가(좋음·보통·나쁨), 추천 이유, 주의점\n"
        "- 순서는 트레이너 목록 API와 같습니다(관장 배지 순 → 사천왕 → 챔피언 → 플라스마단).\n"
        "- 각 항목의 점수와 설명은 포켓몬·트레이너 한 쌍을 평가하는 API와 같습니다.\n\n"
        "**평가 범위**\n"
        "- 포켓몬 자신의 타입을 공격 타입으로 가정합니다. 실제 보유 기술·특성·능력치·레벨은 반영하지 않습니다.\n"
        "- 점수는 승률이 아니며, 현재 포획 가능 여부나 승리를 보장하지 않습니다."
    ),
    response_description="포켓몬 정보와 트레이너별 상성 점수·평가·설명",
    responses={
        404: {"description": "등록되지 않은 포켓몬 ID입니다."},
        422: {"description": "음수·정수가 아닌 포켓몬 ID 또는 지원하지 않는 분류입니다."},
        500: {"description": "데이터 읽기 실패, 잘못된 포켓몬 참조·타입 또는 빈 상대 파티 등 서버 데이터 오류입니다."},
    },
)
def get_trainer_evaluations(
    pokemon_id: int = Path(ge=0, description="하나도감 기준 포켓몬 ID. 0(비크티니)도 유효합니다.", examples=[16]),
    category: TrainerCategory | None = Query(
        default=None,
        description="`gym-leader`, `elite-four`, `champion`, `plasma` 중 하나. 보내지 않으면 전체입니다.",
        examples=["gym-leader"],
    ),
):
    try:
        return recommendation_service.get_trainer_evaluations(pokemon_id, category)
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise HTTPException(status_code=500, detail="추천 계산에 필요한 데이터가 올바르지 않습니다.") from error
