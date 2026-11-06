import json
from pathlib import Path

# 임시 데이터. 실제 데이터가 오면 이 파일의 읽는 부분만 수정합니다.
DATA_FILE = Path(__file__).resolve().parents[3] / "data" / "mock_trainers.json"


def _load_data():
    with DATA_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def get_trainers(category: str | None = None):
    trainers = _load_data()
    if category is None:
        return trainers
    return [trainer for trainer in trainers if trainer["category"] == category]


def get_trainer(trainer_id: str):
    """해당 ID의 관장·사천왕이 없으면 None을 반환합니다."""
    for trainer in _load_data():
        if trainer["id"] == trainer_id:
            return trainer
    return None