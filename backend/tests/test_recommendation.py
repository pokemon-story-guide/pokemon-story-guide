import unittest

from algorithm import recommendation
from algorithm.recommendation import evaluate_against_party, rank_candidates

# 카밀레(전기) 파티: 에몽가(전기·비행) x2, 제브라이카(전기)
ELESA_PARTY = [
    {"pokemon_id": 93, "level": 25, "types": ["electric", "flying"]},
    {"pokemon_id": 93, "level": 25, "types": ["electric", "flying"]},
    {"pokemon_id": 29, "level": 27, "types": ["electric"]},
]


class EvaluateAgainstPartyTest(unittest.TestCase):
    def test_ground_type_against_electric_party(self):
        # 땅: 에몽가(비행)에는 공격 무효(-1) + 비행 공격 1배(0) = -1
        #     제브라이카에는 공격 2배(+1) + 전기 공격 무효(+2) = 3
        result = evaluate_against_party(["ground"], ELESA_PARTY)
        self.assertEqual([d["points"] for d in result["details"]], [-1, -1, 3])
        self.assertEqual(result["score"], 54)  # 50 + (1/3) * 12.5
        self.assertEqual(result["rating"], "normal")
        self.assertEqual(result["summary"]["advantage_count"], 1)
        self.assertEqual(result["summary"]["weak_to_count"], 0)

    def test_water_flying_is_bad_against_electric(self):
        # 물·비행: 전기에 4배 약점
        result = evaluate_against_party(["water", "flying"], ELESA_PARTY)
        self.assertEqual(result["details"][2]["defense_multiplier"], 4)
        self.assertEqual(result["details"][2]["threat_type"], "electric")
        self.assertEqual(result["rating"], "bad")
        self.assertEqual(result["summary"]["weak_to_count"], 3)

    def test_neutral_matchup_is_fifty(self):
        result = evaluate_against_party(["normal"], [{"types": ["normal"]}])
        self.assertEqual(result["score"], 50)
        self.assertEqual(result["rating_label"], "보통")

    def test_details_keep_opponent_info(self):
        result = evaluate_against_party(["ground"], ELESA_PARTY)
        detail = result["details"][2]
        self.assertEqual(detail["pokemon_id"], 29)
        self.assertEqual(detail["level"], 27)
        self.assertEqual(detail["best_attack_type"], "ground")

    def test_score_is_clamped_to_range(self):
        best = evaluate_against_party(["ground"], [{"types": ["fire", "rock"]}] * 2)
        self.assertLessEqual(best["score"], 100)
        self.assertGreaterEqual(best["score"], 0)

    def test_empty_party(self):
        with self.assertRaises(ValueError):
            evaluate_against_party(["water"], [])

    def test_rating_boundaries(self):
        self.assertEqual(recommendation._to_rating(65)[0], "good")
        self.assertEqual(recommendation._to_rating(64)[0], "normal")
        self.assertEqual(recommendation._to_rating(40)[0], "normal")
        self.assertEqual(recommendation._to_rating(39)[0], "bad")


class RankCandidatesTest(unittest.TestCase):
    def test_sorted_by_score(self):
        candidates = [
            {"id": 86, "name": "꼬지보리", "types": ["water", "flying"]},
            {"id": 35, "name": "두더류", "types": ["ground"]},
            {"id": 10, "name": "보르쥐", "types": ["normal"]},
        ]
        ranked = rank_candidates(candidates, ELESA_PARTY)
        self.assertEqual([item["id"] for item in ranked], [35, 10, 86])
        self.assertEqual(ranked[0]["name"], "두더류")

    def test_same_result_as_single_evaluation(self):
        ranked = rank_candidates([{"id": 35, "types": ["ground"]}], ELESA_PARTY)
        single = evaluate_against_party(["ground"], ELESA_PARTY)
        self.assertEqual(ranked[0]["score"], single["score"])


if __name__ == "__main__":
    unittest.main()