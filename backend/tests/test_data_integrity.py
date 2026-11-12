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



TRAINER_DIR = DATA_DIR / "trainers"

TRAINER_CATEGORY_BY_FOLDER = {
    "gym_leaders": "gym-leader",
    "elite_four": "elite-four",
    "n": "rival",
}

TRAINER_REQUIRED_FIELDS = {"id", "name", "category", "type", "image", "party"}
TRAINER_OPTIONAL_FIELDS = {"badge_order"}


class TrainerDataIntegrityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pokemon = json.loads((DATA_DIR / "mon.json").read_text(encoding="utf-8"))
        cls.pokemon_ids = {entry["id"] for entry in pokemon}

        cls.trainers = []
        for folder in TRAINER_CATEGORY_BY_FOLDER:
            for path in sorted((TRAINER_DIR / folder).glob("*.json")):
                trainer = json.loads(path.read_text(encoding="utf-8"))
                cls.trainers.append((path.name, folder, trainer))

    def test_every_folder_has_trainers(self):
        for folder in TRAINER_CATEGORY_BY_FOLDER:
            with self.subTest(folder=folder):
                count = sum(1 for _, name, _ in self.trainers if name == folder)
                self.assertGreater(count, 0, f"인물 데이터가 없는 폴더: {folder}")

    def test_trainer_fields_match_schema(self):
        allowed = TRAINER_REQUIRED_FIELDS | TRAINER_OPTIONAL_FIELDS
        for file_name, folder, trainer in self.trainers:
            with self.subTest(file=file_name):
                keys = set(trainer)
                self.assertFalse(TRAINER_REQUIRED_FIELDS - keys,
                                 f"빠진 필드: {TRAINER_REQUIRED_FIELDS - keys}")
                self.assertFalse(keys - allowed, f"스키마에 없는 필드: {keys - allowed}")

                self.assertIsInstance(trainer["id"], str)
                self.assertTrue(trainer["id"].strip())
                self.assertIsInstance(trainer["name"], str)
                self.assertTrue(trainer["name"].strip())
                self.assertIsInstance(trainer["image"], str)
                self.assertEqual(trainer["category"], TRAINER_CATEGORY_BY_FOLDER[folder])


                if trainer["category"] == "rival":
                    self.assertIn(trainer["type"], ("", *TYPES))
                else:
                    self.assertIn(trainer["type"], TYPES)


                if trainer["category"] == "gym-leader":
                    self.assertIs(type(trainer.get("badge_order")), int)
                    self.assertIn(trainer["badge_order"], range(1, 9))
                else:
                    self.assertNotIn("badge_order", trainer)

    def test_trainer_ids_are_unique(self):
        ids = [trainer["id"] for _, _, trainer in self.trainers]
        duplicates = {value for value in ids if ids.count(value) > 1}
        self.assertFalse(duplicates, f"인물 ID 중복: {duplicates}")

    def test_party_references_existing_pokemon(self):
        for file_name, _, trainer in self.trainers:
            party = trainer["party"]
            with self.subTest(file=file_name):
                self.assertIsInstance(party, list)
                self.assertTrue(party, "파티가 비어 있음")
            for slot, member in enumerate(party, start=1):
                with self.subTest(file=file_name, slot=slot):
                    self.assertEqual(set(member), {"pokemon_id", "level"})
                    self.assertIs(type(member["pokemon_id"]), int)
                    self.assertTrue(member["pokemon_id"] in self.pokemon_ids,
                                    f"mon.json에 없는 포켓몬 ID: {member['pokemon_id']}")
                    self.assertIs(type(member["level"]), int)
                    self.assertIn(member["level"], range(1, 101))