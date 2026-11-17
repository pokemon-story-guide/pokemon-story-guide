import json
from pathlib import Path

# 관장·사천왕 데이터 폴더. 인물 한 명당 JSON 파일 하나입니다.
DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "trainers"

# 데이터 담당이 제공한 관장·사천왕·N 폴더를 읽습니다.
CATEGORY_DIRS = ["gym_leaders", "elite_four", "n"]


def _load_data():
    trainers = []
    for folder in CATEGORY_DIRS:
        folder_path = DATA_DIR / folder
        # 필수 폴더가 없거나 비어 있으면 빈 목록으로 숨기지 않고 오류를 냅니다.
        if not folder_path.is_dir():
            raise FileNotFoundError(f"관장 데이터 폴더가 없습니다: {folder_path}")
        paths = sorted(folder_path.glob("*.json"))
        if not paths:
            raise FileNotFoundError(f"관장 데이터 폴더가 비어 있습니다: {folder_path}")
        for path in paths:
            with path.open(encoding="utf-8") as file:
                trainers.append(json.load(file))
    return trainers


def get_trainers(category: str | None = None):
    trainers = _load_data()
    if category is None:
        return trainers
    return [trainer for trainer in trainers if trainer["category"] == category]


def get_trainer(trainer_id: str):
    """해당 ID의 인물이 없으면 None을 반환합니다."""
    for trainer in _load_data():
        if trainer["id"] == trainer_id:
            return trainer
    return None