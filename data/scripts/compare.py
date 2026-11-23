"""두 폴더의 mon.json / move.json / learn.json을 비교해 달라진 값을 출력합니다. 테스트를 위한 스크립트입니다."""

import json
import sys
from pathlib import Path


def load(folder: Path, name: str) -> list:
    return json.loads((folder / name).read_text(encoding="utf-8"))


def normalize_evolution(value):
    if not value:
        return None
    return sorted((row["id"], str(row["condition"])) for row in value)


def compare_rows(label: str, old_rows: list, new_rows: list, key: str, fields: list[str], convert=None):
    old_by_id = {row[key]: row for row in old_rows}
    new_by_id = {row[key]: row for row in new_rows}
    diffs = 0
    for row_id in sorted(old_by_id.keys() | new_by_id.keys()):
        old, new = old_by_id.get(row_id), new_by_id.get(row_id)
        if old is None or new is None:
            print(f"[{label}] {row_id}: {'새로 생김' if old is None else '없어짐'}")
            diffs += 1
            continue
        for field in fields:
            a, b = old.get(field), new.get(field)
            if convert and field in convert:
                a, b = convert[field](a), convert[field](b)
            if a != b:
                name = old.get("name", "")
                print(f"[{label}] {row_id} {name} {field}: {a!r} -> {b!r}")
                diffs += 1
    print(f"== {label}: 차이 {diffs}건 / 전체 {len(old_by_id)}건\n")


def main():
    if len(sys.argv) != 3:
        sys.exit("사용법: python data/scripts/compare.py <기존 폴더> <새 폴더>")
    old_dir, new_dir = Path(sys.argv[1]), Path(sys.argv[2])

    compare_rows(
        "mon", load(old_dir, "mon.json"), load(new_dir, "mon.json"), "id",
        ["name", "types", "base_stat_total", "location_ids", "evolution_from", "evolution_to", "usable"],
        convert={"evolution_from": normalize_evolution, "evolution_to": normalize_evolution},
    )
    compare_rows(
        "move", load(old_dir, "move.json"), load(new_dir, "move.json"), "id",
        ["name", "type", "expected_power"],
    )
    as_set = lambda moves: sorted((m["level"], m["move_id"]) for m in moves)
    compare_rows(
        "learn", load(old_dir, "learn.json"), load(new_dir, "learn.json"), "pokemon_id",
        ["moves"], convert={"moves": as_set},
    )


if __name__ == "__main__":
    main()
