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


if __name__ == "__main__":
    unittest.main()