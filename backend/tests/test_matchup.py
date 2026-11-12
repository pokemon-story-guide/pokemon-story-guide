import unittest

from algorithm.matchup import get_defense_matchups, get_offense_matchups, get_pokemon_matchups


def _types(entries):
    return {entry["type"]: entry["multiplier"] for entry in entries}


class PokemonMatchupTest(unittest.TestCase):
    def test_defense_single_type(self):
        result = get_defense_matchups(["fire"])
        self.assertEqual(_types(result["weak"]), {"water": 2, "ground": 2, "rock": 2})
        self.assertIn("grass", _types(result["resist"]))
        self.assertEqual(result["immune"], [])

    def test_defense_dual_type_four_times_and_quarter(self):
        result = get_defense_matchups(["water", "ground"])  # 두빅굴
        self.assertEqual(_types(result["weak"]), {"grass": 4})
        self.assertEqual(_types(result["immune"]), {"electric": 0})

        result = get_defense_matchups(["bug", "steel"])  # 슈바르고
        self.assertEqual(_types(result["weak"]), {"fire": 4})
        self.assertEqual(_types(result["resist"])["grass"], 0.25)
        self.assertEqual(_types(result["immune"]), {"poison": 0})

    def test_defense_covers_all_types_once(self):
        result = get_defense_matchups(["normal", "flying"])
        all_types = [entry["type"] for group in result.values() for entry in group]
        self.assertEqual(len(all_types), 17)
        self.assertEqual(len(set(all_types)), 17)
        self.assertEqual(_types(result["immune"]), {"ground": 0, "ghost": 0})

    def test_offense_uses_best_of_own_types(self):
        result = get_offense_matchups(["fire", "fighting"])  # 염무왕
        strong = _types(result["strong"])
        self.assertEqual(strong["normal"], 2)
        self.assertEqual(strong["grass"], 2)
        self.assertEqual(_types(result["neutral"])["ghost"], 1)  # 격투는 무효지만 불꽃은 1배

    def test_offense_no_effect(self):
        result = get_offense_matchups(["normal"])
        self.assertEqual(_types(result["no_effect"]), {"ghost": 0})
        self.assertEqual(result["strong"], [])

    def test_pokemon_matchups_shape(self):
        result = get_pokemon_matchups(["water"])
        self.assertEqual(result["types"], ["water"])
        self.assertEqual(set(result), {"types", "defense", "offense"})

    def test_invalid_types(self):
        with self.assertRaises(ValueError):
            get_pokemon_matchups([])
        with self.assertRaises(ValueError):
            get_pokemon_matchups(["fairy"])


if __name__ == "__main__":
    unittest.main()