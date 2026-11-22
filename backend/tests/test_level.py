import unittest

from algorithm.level import get_recommended_level

# 카밀레 파티: 에몽가 Lv.25 x2, 제브라이카 Lv.27
ELESA_PARTY = [
    {"pokemon_id": 93, "level": 25},
    {"pokemon_id": 93, "level": 25},
    {"pokemon_id": 29, "level": 27},
]


class RecommendedLevelTest(unittest.TestCase):
    def test_uses_max_party_level(self):
        result = get_recommended_level(ELESA_PARTY)
        self.assertEqual(result["recommended_level"], 27)
        self.assertEqual(result["basis"], "max_party_level")

    def test_returns_party_level_summary(self):
        result = get_recommended_level(ELESA_PARTY)
        self.assertEqual(result["party_max_level"], 27)
        self.assertEqual(result["party_min_level"], 25)
        self.assertEqual(result["party_average_level"], 25.7)

    def test_single_pokemon_party(self):
        result = get_recommended_level([{"level": 7}])
        self.assertEqual(result["recommended_level"], 7)

    def test_empty_party(self):
        with self.assertRaises(ValueError):
            get_recommended_level([])


if __name__ == "__main__":
    unittest.main()