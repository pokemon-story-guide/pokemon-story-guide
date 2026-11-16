import unittest

from scripts.build_type_chart import TYPES, build_type_chart, select_relations, to_attack_multipliers


def _relations(no=(), half=(), double=()):
    names = lambda items: [{"name": name} for name in items]
    return {"no_damage_to": names(no), "half_damage_to": names(half), "double_damage_to": names(double)}


class BuildTypeChartTest(unittest.TestCase):
    def test_uses_current_when_no_past_record(self):
        data = {"damage_relations": _relations(double=["grass"]), "past_damage_relations": []}
        self.assertEqual(select_relations(data), data["damage_relations"])

    def test_uses_earliest_past_record_for_gen5(self):
        gen5 = _relations(half=["ghost", "dark"])
        data = {
            "damage_relations": _relations(),
            "past_damage_relations": [
                {"generation": {"name": "generation-v"}, "damage_relations": gen5},
            ],
        }
        self.assertEqual(select_relations(data), gen5)

    def test_ignores_records_before_gen5(self):
        old = _relations(double=["ghost"])
        data = {
            "damage_relations": _relations(),
            "past_damage_relations": [{"generation": {"name": "generation-i"}, "damage_relations": old}],
        }
        self.assertEqual(select_relations(data), data["damage_relations"])

    def test_excludes_types_not_in_gen5(self):
        result = to_attack_multipliers(_relations(no=["fairy"], double=["dragon", "fairy"]))
        self.assertEqual(result, {"dragon": 2})

    def test_build_with_fake_fetch(self):
        chart = build_type_chart(lambda name: {"damage_relations": _relations(), "past_damage_relations": []})
        self.assertEqual(set(chart), set(TYPES))


if __name__ == "__main__":
    unittest.main()