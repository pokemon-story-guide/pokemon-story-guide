from fastapi import APIRouter, HTTPException
from api.services.data_loader import load_trainers
from api.schemas.trainer import TrainerSummary, TrainerDetail

router = APIRouter(prefix="/trainers", tags=["trainers"])

@router.get("", response_model=list[TrainerSummary])
def list_trainers(category: str | None = None):
    result = []
    for trainer in load_trainers():
        if category and trainer["category"] != category:
            continue
        result.append({
            "id": trainer["id"],
            "name": trainer["name"],
            "category": trainer["category"],
            "type": trainer["type"],
            "badge_order": trainer.get("badge_order"),
            "image": trainer["image"],
        })
    return result

@router.get("/{trainer_id}", response_model=TrainerDetail,responses={404: {"description": "해당 관장·사천왕이 없음"}})
def get_trainer(trainer_id: str):
    for trainer in load_trainers():
        if trainer["id"] == trainer_id:
            return trainer
    raise HTTPException(status_code=404, detail="Trainer not found")