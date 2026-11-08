import json
from pathlib import Path
import unittest

from algorithm.type_chart import TYPES

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class DataIntegrityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.places = json.loads((DATA_DIR / "place.json").read_text(encoding="utf-8"))
        cls.pokemon = json.loads((DATA_DIR / "mon.json").read_text(encoding="utf-8"))

    def test_place_fields_and_unique_ids(self):
        self.assertTrue(self.places)
        ids = []
        for place in self.places:
            with self.subTest(place=place):
                self.assertIs(type(place["id"]), int)
                self.assertIsInstance(place["name"], str)
                self.assertTrue(place["name"].strip())
                ids.append(place["id"])
        self.assertEqual(len(ids), len(set(ids)), "장소 ID 중복")

    def test_pokemon_fields_types_and_unique_ids(self):
        self.assertTrue(self.pokemon)
        ids = []
        for pokemon in self.pokemon:
            with self.subTest(pokemon=pokemon.get("id")):
                self.assertIs(type(pokemon["id"]), int)
                self.assertIsInstance(pokemon["name"], str)
                self.assertTrue(pokemon["name"].strip())
                types = pokemon["types"]
                self.assertIsInstance(types, list)
                self.assertIn(len(types), (1, 2))
                self.assertEqual(len(types), len(set(types)))
                self.assertLessEqual(set(types), set(TYPES))
                ids.append(pokemon["id"])
        self.assertEqual(len(ids), len(set(ids)), "포켓몬 ID 중복")

    def test_location_references(self):
        place_ids = {place["id"] for place in self.places}
        for pokemon in self.pokemon:
            with self.subTest(pokemon=pokemon["id"], name=pokemon["name"]):
                locations = pokemon["location_ids"]
                if locations is None:
                    continue
                self.assertIsInstance(locations, list)
                self.assertTrue(all(type(value) is int for value in locations))
                self.assertEqual(len(locations), len(set(locations)), "장소 참조 중복")
                self.assertFalse(set(locations) - place_ids,
                                 f"존재하지 않는 장소 ID: {set(locations) - place_ids}")
