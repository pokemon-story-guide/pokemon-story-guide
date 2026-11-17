import unittest

from algorithm.type_chart import TYPE_CHART, TYPES, get_multiplier


class TypeChartTest(unittest.TestCase):
    def test_chart_has_17_types_without_fairy(self):
        self.assertEqual(len(TYPES), 17)
        self.assertEqual(set(TYPE_CHART), set(TYPES))
        self.assertNotIn("fairy", TYPES)

    def test_chart_values_are_valid(self):
        for matchups in TYPE_CHART.values():
            self.assertLessEqual(set(matchups), set(TYPES))
            self.assertLessEqual(set(matchups.values()), {0, 0.5, 2})

    def test_multipliers(self):
        cases = [
            ("water", ["fire"], 2),
            ("fire", ["water"], 0.5),
            ("electric", ["ground"], 0),
            ("normal", ["water"], 1),           
            ("dragon", ["fire"], 1),
            ("ghost", ["steel"], 0.5),        
            ("dark", ["steel"], 0.5),            
            ("ice", ["dragon", "flying"], 4),
            ("grass", ["fire", "flying"], 0.25),
            ("bug", ["fire", "fighting"], 0.25),
            ("ice", ["water", "ground"], 1),    
            ("water", ["ground", "flying"], 2),
            ("ground", ["electric", "flying"], 0),
            ("fighting", ["normal", "ghost"], 0),
        ]
        for attack_type, defense_types, expected in cases:
            with self.subTest(attack=attack_type, defense=defense_types):
                self.assertEqual(get_multiplier(attack_type, defense_types), expected)

    def test_invalid_input(self):
        cases = [("fairy", ["normal"]), ("water", ["fairy"]), ("water", [])]
        for attack_type, defense_types in cases:
            with self.subTest(attack=attack_type, defense=defense_types):
                with self.assertRaises(ValueError):
                    get_multiplier(attack_type, defense_types)


if __name__ == "__main__":
    unittest.main()