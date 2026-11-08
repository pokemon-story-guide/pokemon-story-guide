import json
from pathlib import Path

# 관장·사천왕 데이터 폴더. 인물 한 명당 JSON 파일 하나입니다.
DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "trainers"

# 데이터 담당이 제공한 관장·사천왕·N 폴더를 읽습니다.
CATEGORY_DIRS = ["gym_leaders", "elite_four", "n"]


def _load_data():
    trainers = []
    for folder in CATEGORY_DIRS:
        for path in sorted((DATA_DIR / folder).glob("*.json")):
            with path.open(encoding="utf-8") as file:
                trainers.append(json.load(file))
    return trainers


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