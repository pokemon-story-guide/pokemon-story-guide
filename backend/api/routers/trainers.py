from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from api.schemas.trainer import TrainerCategory, TrainerSummary, TrainerDetail
from api.services import trainer_service

router = APIRouter(prefix="/trainers", tags=["trainers"])

DATA_ERROR_RESPONSE = {
    "description": "관장 데이터 폴더가 없거나 비어 있는 등 서버 데이터 오류입니다."
}


@router.get(
    "",
    response_model=list[TrainerSummary],
    summary="관장·사천왕·N 카드 목록 조회",
    description=(
        "인물 선택 화면에서 사용할 카드 목록을 조회합니다.\n\n"
        "**분류**\n"
        "- `gym-leader`: 관장\n"
        "- `elite-four`: 사천왕\n"
        "- `rival`: N (스토리 중 여러 장소에서 대전)\n"
        "- 분류를 생략하면 전체를 반환합니다.\n\n"
        "**정렬**\n"
        "- 관장 → 사천왕 → N 순서입니다.\n"
        "- 관장은 배지 순서, N은 스토리 순서입니다.\n"
        "- 1번 체육관(팟·덴트·콘)과 8번 체육관(사간·아이리스)은 같은 `badge_order`를 가집니다.\n\n"
        "**결과**\n"
        "- 카드에 필요한 기본 정보만 반환합니다. 파티는 상세 조회에서 확인합니다."
    ),
    response_description="분류 조건에 맞는 인물 카드 목록",
    responses={
        422: {"description": "허용되지 않는 분류 값을 입력한 경우입니다."},
        500: DATA_ERROR_RESPONSE,
    },
)
def list_trainers(
    category: TrainerCategory | None = Query(
        default=None,
        description=(
            "**분류 (선택)**\n\n"
            "- `gym-leader`, `elite-four`, `rival` 중 하나를 선택합니다.\n"
            "- 전체를 보려면 값을 보내지 마세요."
        ),
        examples=["gym-leader"],
    ),
):
    return trainer_service.get_trainers(category)


@router.get(
    "/{trainer_id}",
    response_model=TrainerDetail,
    summary="관장·사천왕·N 상세 조회",
    description=(
        "선택한 인물의 기본 정보와 보유 파티를 조회합니다.\n\n"
        "**공통 상세**\n"
        "- 관장·사천왕·N 모두 같은 응답 구조를 사용합니다.\n"
        "- 사천왕과 N은 `badge_order`가 `null`입니다.\n\n"
        "**보유 파티**\n"
        "- 배틀에서 사용하는 포켓몬의 ID(하나도감 기준)와 레벨을 반환합니다.\n"
        "- 포켓몬 이름·타입은 같은 ID로 포켓몬 상세 API에서 확인할 수 있습니다."
    ),
    response_description="인물 기본 정보와 보유 파티",
    responses={
        404: {"description": "등록된 인물이 없는 ID입니다."},
        500: DATA_ERROR_RESPONSE,
    },
)
def get_trainer(
    trainer_id: Annotated[str, Path(
        description=(
            "**인물 ID (필수)**\n\n"
            "- 목록 API에서 받은 `id`를 입력합니다.\n"
            "- 예: `elesa` = 카밀레, `shauntal` = 망초, `n-accumula-town` = N (넝쿨마을)"
        ),
        examples=["elesa"],
    )],
):
    trainer = trainer_service.get_trainer(trainer_id)
    if trainer is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 인물입니다.")
    return trainer