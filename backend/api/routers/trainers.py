from fastapi import APIRouter, HTTPException

from api.schemas.trainer import TrainerSummary, TrainerDetail
from api.services import trainer_service

router = APIRouter(prefix="/trainers", tags=["trainers"])


@router.get("", response_model=list[TrainerSummary])
def list_trainers(category: str | None = None):
    return trainer_service.get_trainers(category)


@router.get(
    "/{trainer_id}",
    response_model=TrainerDetail,
    responses={404: {"description": "해당 관장·사천왕이 없음"}},
)
def get_trainer(trainer_id: str):
    trainer = trainer_service.get_trainer(trainer_id)
    if trainer is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 관장·사천왕입니다.")
    return trainer