import unittest

from algorithm.matchup import get_defense_matchups, get_offense_matchups, get_pokemon_matchups


def _types(entries):
    return {entry["type"]: entry["multiplier"] for entry in entries}

class PokemonMatchupTest(unittest.TestCase):
    def test_defense_matchups(self):
        cases = [
            (["fire"], "weak", {"water": 2, "ground": 2, "rock": 2}),
            (["fire"], "immune", {}),
            (["water", "ground"], "weak", {"grass": 4}),          
            (["water", "ground"], "immune", {"electric": 0}),
            (["bug", "steel"], "weak", {"fire": 4}),             
            (["bug", "steel"], "immune", {"poison": 0}),
            (["normal", "flying"], "immune", {"ground": 0, "ghost": 0}),
        ]
        for types, group, expected in cases:
            with self.subTest(types=types, group=group):
                self.assertEqual(_types(get_defense_matchups(types)[group]), expected)

    def test_defense_quarter_resist(self):
        resist = _types(get_defense_matchups(["bug", "steel"])["resist"])
        self.assertEqual(resist["grass"], 0.25)

    def test_offense_matchups(self):
        cases = [
            (["normal"], "no_effect", {"ghost": 0}),
            (["normal"], "strong", {}),
            (["fire", "fighting"], "no_effect", {}), 
        ]
        for types, group, expected in cases:
            with self.subTest(types=types, group=group):
                self.assertEqual(_types(get_offense_matchups(types)[group]), expected)

    def test_offense_uses_best_of_own_types(self):
        strong = _types(get_offense_matchups(["fire", "fighting"])["strong"])  
        self.assertEqual(strong["normal"], 2)
        self.assertEqual(strong["grass"], 2)

    def test_each_type_appears_once(self):
        for result in (get_defense_matchups(["normal", "flying"]), get_offense_matchups(["water"])):
            all_types = [entry["type"] for group in result.values() for entry in group]
            self.assertEqual(len(all_types), 17)
            self.assertEqual(len(set(all_types)), 17)

    def test_pokemon_matchups_shape(self):
        result = get_pokemon_matchups(["water"])
        self.assertEqual(result["types"], ["water"])
        self.assertEqual(set(result), {"types", "defense", "offense"})
        self.assertEqual(set(result["defense"]), {"weak", "resist", "immune", "neutral"})
        self.assertEqual(set(result["offense"]), {"strong", "weak", "no_effect", "neutral"})

    def test_invalid_types(self):
        for types in ([], ["fairy"]):
            with self.subTest(types=types):
                with self.assertRaises(ValueError):
                    get_pokemon_matchups(types)


if __name__ == "__main__":
    unittest.main()