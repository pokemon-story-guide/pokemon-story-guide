import json
import urllib.request
from pathlib import Path

API_URL = "https://pokeapi.co/api/v2/type/{name}"
OUTPUT_PATH = Path(__file__).resolve().parents[2] / "data" / "type_chart.json"
TARGET_GENERATION = 5

TYPES = (
    "normal", "fire", "water", "electric", "grass", "ice",
    "fighting", "poison", "ground", "flying", "psychic", "bug",
    "rock", "ghost", "dragon", "dark", "steel",
)

ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9}


def fetch_type(name: str) -> dict:
    request = urllib.request.Request(API_URL.format(name=name), headers={"User-Agent": "pokemon-story-guide"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _generation_number(generation: dict) -> int:
    return ROMAN[generation["name"].removeprefix("generation-")]


def select_relations(type_data: dict, generation: int = TARGET_GENERATION) -> dict:
    past = [
        item for item in type_data.get("past_damage_relations", [])
        if _generation_number(item["generation"]) >= generation
    ]
    if past:
        return min(past, key=lambda item: _generation_number(item["generation"]))["damage_relations"]
    return type_data["damage_relations"]


def to_attack_multipliers(relations: dict) -> dict:
    result = {}
    for key, multiplier in (("no_damage_to", 0), ("half_damage_to", 0.5), ("double_damage_to", 2)):
        for target in relations[key]:
            if target["name"] in TYPES:
                result[target["name"]] = multiplier
    return dict(sorted(result.items(), key=lambda item: TYPES.index(item[0])))


def build_type_chart(fetch=fetch_type) -> dict:
    return {name: to_attack_multipliers(select_relations(fetch(name))) for name in TYPES}


def main():
    chart = build_type_chart()
    OUTPUT_PATH.write_text(json.dumps(chart, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()