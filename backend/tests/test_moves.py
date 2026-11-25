import unittest

from algorithm import moves
from algorithm.moves import get_learnable_moves, recommend_moves

TACKLE = {"id": 1, "name": "몸통박치기", "type": "normal", "expected_power": 50}
EMBER = {"id": 2, "name": "불꽃세례", "type": "fire", "expected_power": 40}
FLAMETHROWER = {"id": 3, "name": "화염방사", "type": "fire", "expected_power": 95}
WATER_GUN = {"id": 4, "name": "물대포", "type": "water", "expected_power": 40}
BITE = {"id": 5, "name": "물기", "type": "dark", "expected_power": 60}
GROWL = {"id": 6, "name": "울음소리", "type": "normal", "expected_power": 0}
LOW_KICK = {"id": 7, "name": "로킥", "type": "fighting", "expected_power": 1}
EARTHQUAKE = {"id": 8, "name": "지진", "type": "ground", "expected_power": 100}

ALL_MOVES = [TACKLE, EMBER, FLAMETHROWER, WATER_GUN, BITE, GROWL, LOW_KICK, EARTHQUAKE]
GRASS_PARTY = [{"types": ["grass"]}, {"types": ["grass", "poison"]}]
FLYING_PARTY = [{"types": ["flying"]}]


def _ids(result):
    return [move["id"] for move in result]


class RecommendMovesTest(unittest.TestCase):
    def test_excludes_status_and_variable_power(self):
        ids = _ids(recommend_moves(["fire"], ALL_MOVES))
        self.assertNotIn(GROWL["id"], ids)
        self.assertNotIn(LOW_KICK["id"], ids)

    def test_returns_at_most_four(self):
        self.assertLessEqual(len(recommend_moves(["fire"], ALL_MOVES)), 4)

    def test_applies_stab(self):
        result = {m["id"]: m for m in recommend_moves(["fire"], ALL_MOVES)}
        self.assertTrue(result[FLAMETHROWER["id"]]["stab"])
        self.assertEqual(result[FLAMETHROWER["id"]]["score"], 95 * 1.5)

    def test_uses_opponent_matchup(self):
        result = recommend_moves(["normal"], [FLAMETHROWER, WATER_GUN], GRASS_PARTY, limit=1)
        self.assertEqual(_ids(result), [FLAMETHROWER["id"]])
        self.assertEqual(result[0]["super_effective_count"], 2)

    def test_excludes_no_effect_moves(self):
        result = recommend_moves(["ground"], [EARTHQUAKE, TACKLE], FLYING_PARTY)
        self.assertEqual(_ids(result), [TACKLE["id"]])

    def test_prefers_different_types(self):
        result = recommend_moves(["fire"], [FLAMETHROWER, EMBER, BITE, TACKLE, WATER_GUN], limit=3)
        self.assertEqual(len({move["type"] for move in result}), 3)
        self.assertNotIn(EMBER["id"], _ids(result))

    def test_fills_with_same_type_when_needed(self):
        result = recommend_moves(["fire"], [FLAMETHROWER, EMBER])
        self.assertEqual(set(_ids(result)), {FLAMETHROWER["id"], EMBER["id"]})

    def test_coverage_option_can_be_turned_off(self):
        original = moves.PREFER_TYPE_COVERAGE
        try:
            moves.PREFER_TYPE_COVERAGE = False
            result = recommend_moves(["fire"], [FLAMETHROWER, EMBER, TACKLE], limit=2)
            self.assertEqual(_ids(result), [FLAMETHROWER["id"], EMBER["id"]])
        finally:
            moves.PREFER_TYPE_COVERAGE = original

    def test_empty_types(self):
        with self.assertRaises(ValueError):
            recommend_moves([], ALL_MOVES)


class LearnableMovesTest(unittest.TestCase):
    def test_filters_by_level(self):
        all_moves = get_learnable_moves(0)
        low_level = get_learnable_moves(0, level=10)
        self.assertTrue(all(move["learn_level"] <= 10 for move in low_level))
        self.assertLessEqual(len(low_level), len(all_moves))

    def test_has_no_duplicate_moves(self):
        ids = [move["id"] for move in get_learnable_moves(34)]
        self.assertEqual(len(ids), len(set(ids)))

    def test_unknown_pokemon(self):
        with self.assertRaises(KeyError):
            get_learnable_moves(9999)


if __name__ == "__main__":
    unittest.main()