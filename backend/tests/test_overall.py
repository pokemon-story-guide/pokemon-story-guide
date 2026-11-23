import unittest

from algorithm import overall
from algorithm.overall import evaluate_overall
from algorithm.recommendation import evaluate_against_party

FIRE_PARTY = [{"types": ["fire"], "level": 14}]
WATER_PARTY = [{"types": ["water"], "level": 14}]
GRASS_PARTY = [{"types": ["grass"], "level": 14}]
ELECTRIC_PARTY = [{"types": ["electric"], "level": 27}]

OPPONENTS = [
    {"id": "chili", "category": "gym-leader", "badge_order": 1, "party": FIRE_PARTY},
    {"id": "cress", "category": "gym-leader", "badge_order": 1, "party": WATER_PARTY},
    {"id": "cilan", "category": "gym-leader", "badge_order": 1, "party": GRASS_PARTY},
    {"id": "elesa", "category": "gym-leader", "badge_order": 4, "party": ELECTRIC_PARTY},
    {"id": "shauntal", "category": "elite-four", "badge_order": None, "party": [{"types": ["ghost"]}]},
    {"id": "alder", "category": "champion", "party": [{"types": ["bug", "fire"]}]},
    {"id": "ghetsis", "category": "plasma", "party": [{"types": ["dark", "dragon"]}]},
    {"id": "n-accumula-town", "category": "plasma", "party": [{"types": ["dark"]}]},
]


def _score(types, party):
    return evaluate_against_party(types, party)["score"]


class OverallRecommendationTest(unittest.TestCase):
    def test_groups_same_badge_order(self):
        result = evaluate_overall(["water"], OPPONENTS)
        groups = {detail["group"]: detail for detail in result["details"]}
        self.assertEqual(set(groups), {"gym-1", "gym-4", "shauntal", "alder", "ghetsis"})
        self.assertEqual(len(groups["gym-1"]["opponents"]), 3)

        expected = (_score(["water"], FIRE_PARTY) + _score(["water"], WATER_PARTY) + _score(["water"], GRASS_PARTY)) / 3
        self.assertEqual(groups["gym-1"]["score"], round(expected, 1))

    def test_includes_ghetsis_excludes_n(self):
        result = evaluate_overall(["water"], OPPONENTS)
        ids = [item["id"] for detail in result["details"] for item in detail["opponents"]]
        self.assertIn("ghetsis", ids)
        self.assertNotIn("n-accumula-town", ids)

    def test_score_is_equal_weight_average_of_groups(self):
        result = evaluate_overall(["water"], OPPONENTS)
        group_scores = [detail["score"] for detail in result["details"]]
        self.assertEqual(result["score"], round(sum(group_scores) / len(group_scores)))

    def test_summary(self):
        result = evaluate_overall(["ground"], OPPONENTS)
        self.assertEqual(result["summary"]["group_count"], 5)
        self.assertEqual(result["summary"]["best_group"], "gym-4")

    def test_category_weight(self):
        original = dict(overall.CATEGORY_WEIGHTS)
        try:
            overall.CATEGORY_WEIGHTS["champion"] = 3
            result = evaluate_overall(["water"], OPPONENTS)
            alder = next(d for d in result["details"] if d["group"] == "alder")
            self.assertEqual(alder["weight"], 3)
        finally:
            overall.CATEGORY_WEIGHTS.clear()
            overall.CATEGORY_WEIGHTS.update(original)

    def test_no_included_opponents(self):
        with self.assertRaises(ValueError):
            evaluate_overall(["water"], [OPPONENTS[-1]])


if __name__ == "__main__":
    unittest.main()