import json
import unittest
from pathlib import Path

from algorithm.type_chart import TYPE_CHART, TYPES, get_multiplier

TYPE_DATA = Path(__file__).resolve().parents[2] / "data" / "type.json"

class TypeChartTest(unittest.TestCase):
    def test_chart_has_17_types_without_fairy(self):
        self.assertEqual(len(TYPES), 17)
        self.assertEqual(set(TYPE_CHART), set(TYPES))
        self.assertNotIn("fairy", TYPES)

    def test_chart_values_are_valid(self):
        for matchups in TYPE_CHART.values():
            self.assertLessEqual(set(matchups), set(TYPES))
            self.assertLessEqual(set(matchups.values()), {0, 0.5, 2})

    def test_single_type(self):
        self.assertEqual(get_multiplier("water", ["fire"]), 2)
        self.assertEqual(get_multiplier("fire", ["water"]), 0.5)
        self.assertEqual(get_multiplier("normal", ["fire"]), 1)
        self.assertEqual(get_multiplier("electric", ["ground"]), 0)

    def test_gen5_steel_resists_ghost_and_dark(self):
        self.assertEqual(get_multiplier("ghost", ["steel"]), 0.5)
        self.assertEqual(get_multiplier("dark", ["steel"]), 0.5)

    def test_dual_type(self):
        self.assertEqual(get_multiplier("ice", ["dragon", "flying"]), 4)
        self.assertEqual(get_multiplier("grass", ["fire", "flying"]), 0.25)
        self.assertEqual(get_multiplier("water", ["ground", "flying"]), 2)
        self.assertEqual(get_multiplier("ground", ["electric", "flying"]), 0)

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            get_multiplier("fairy", ["normal"])
        with self.assertRaises(ValueError):
            get_multiplier("water", ["fairy"])
        with self.assertRaises(ValueError):
            get_multiplier("water", [])
    def test_matches_type_json_for_all_combinations(self):
        type_data = json.loads(TYPE_DATA.read_text(encoding="utf-8"))
        names = {item["id"]: item["english_name"] for item in type_data}
        self.assertEqual(set(names.values()), set(TYPES))

        for item in type_data:
            attack_type = item["english_name"]
            expected = {names[x["type_id"]]: x["multiplier"] for x in item["attack_multipliers"]}
            for defense_type in TYPES:
                with self.subTest(attack=attack_type, defense=defense_type):
                    self.assertEqual(
                        get_multiplier(attack_type, [defense_type]),
                        expected.get(defense_type, 1),
                    )

    def test_unlisted_combination_is_neutral(self):
        self.assertEqual(get_multiplier("normal", ["water"]), 1)
        self.assertEqual(get_multiplier("dragon", ["fire"]), 1)

    def test_dual_type_cancel_and_immune(self):
        self.assertEqual(get_multiplier("ice", ["water", "ground"]), 1)
        self.assertEqual(get_multiplier("fighting", ["normal", "ghost"]), 0)
        self.assertEqual(get_multiplier("bug", ["fire", "fighting"]), 0.25)

if __name__ == "__main__":
    unittest.main()