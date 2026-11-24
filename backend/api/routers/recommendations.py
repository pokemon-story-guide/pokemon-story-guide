from fastapi import APIRouter, HTTPException, Path, Query

from api.schemas.recommendation import Recommendation, TrainerRecommendations
from api.services import recommendation_service, trainer_recommendation_service

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
    "/trainers/{trainer_id}",
    response_model=TrainerRecommendations,
    summary="선택한 트레이너 상대 추천 포켓몬 목록 조회",
    description=(
        "트레이너 ID만 전달하면 등록된 포켓몬 전체를 상대 파티와 비교해 순위로 반환합니다.\n\n"
        "**사용 방법**\n"
        "- 트레이너 목록 API의 `id`를 사용합니다. 관장·사천왕·챔피언·플라스마 인물 모두 조회할 수 있습니다.\n"
        "- 예: `/api/recommendations/trainers/elesa?limit=10` → 카밀레 상대 상위 10마리\n\n"
        "**정렬과 반환 정보**\n"
        "- 점수 내림차순, 동점이면 포켓몬 ID 오름차순입니다.\n"
        "- 후보별 이름·타입·점수·평가·추천 이유·주의점을 반환합니다.\n"
        "- `total_count`는 제한 전 후보 수이며, 후보가 적으면 limit보다 적게 반환합니다.\n"
        "- 점수가 낮은 후보도 순위에 포함되므로 주의점을 함께 확인해야 합니다.\n\n"
        "**평가 범위**\n"
        "- 후보 자신의 타입으로 공격한다고 가정하고, 상대의 복합 타입과 파티 전체를 평가합니다.\n"
        "- 기존 공통 알고리즘을 사용하며 실제 기술·특성·능력치·레벨은 반영하지 않습니다.\n"
        "- 현재 위치·스토리 진행도에 따른 포획 가능 여부는 반영하지 않습니다. 점수는 승률이 아닙니다."
    ),
    response_description="상대 정보와 후보 포켓몬의 상성 순위·추천 이유·주의점",
    responses={
        404: {"description": "등록되지 않은 트레이너 ID입니다."},
        422: {"description": "공백이 포함된 트레이너 ID 또는 1~50 범위의 정수가 아닌 limit입니다."},
        500: {"description": "데이터 읽기 실패, 중복 ID, 잘못된 타입·파티 참조 또는 빈 상대 파티입니다."},
    },
)
def get_trainer_recommendations(
    trainer_id: str = Path(min_length=1, pattern=r"^\S+$", description="트레이너 목록에서 받은 상대 ID.", examples=["elesa"]),
    limit: int = Query(default=10, ge=1, le=50, description="반환할 추천 개수. 기본 10개, 최대 50개.", examples=[10]),
):
    try:
        return trainer_recommendation_service.get_trainer_recommendations(trainer_id, limit)
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise HTTPException(status_code=500, detail="추천 계산에 필요한 데이터가 올바르지 않습니다.") from error
