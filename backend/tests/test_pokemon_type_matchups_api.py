import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from algorithm.type_chart import TYPES
from api.main import app


def multipliers(entries):
    return {entry["type"]: entry["multiplier"] for entry in entries}


class PokemonTypeMatchupsApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.pokemon = [
            {"id": 0, "types": ["water", "ground"]},
            {"id": 1, "types": ["bug", "steel"]},
            {"id": 2, "types": ["normal"]},
            {"id": 3, "types": ["fire", "fighting"]},
        ]
        loader = patch("api.services.pokemon_service._load_pokemon", return_value=self.pokemon)
        self.loader = loader.start()
        self.addCleanup(loader.stop)

    def get_matchups(self, pokemon_id=0):
        return self.client.get(f"/api/pokemon/{pokemon_id}/type-matchups")

    def test_id_only_request_returns_public_fields_and_database_types(self):
        response = self.get_matchups()
        self.assertEqual(response.status_code, 200)
        row = response.json()
        self.assertEqual(set(row), {"pokemon_id", "types", "defense", "offense", "evaluation_basis"})
        self.assertEqual(row["pokemon_id"], 0)
        self.assertEqual(row["types"], ["water", "ground"])
        self.assertEqual(set(row["defense"]), {"weak", "resist", "immune", "neutral"})
        self.assertEqual(set(row["offense"]), {"strong", "weak", "no_effect", "neutral"})
        self.assertIn("실제 기술", row["evaluation_basis"])
        self.assertIn("상대 단일 타입", row["evaluation_basis"])

    def test_double_type_defense_returns_four_times_weakness_and_immunity(self):
        defense = self.get_matchups().json()["defense"]
        self.assertEqual(multipliers(defense["weak"]), {"grass": 4})
        self.assertEqual(multipliers(defense["immune"]), {"electric": 0})

    def test_quarter_resistance_is_preserved(self):
        defense = self.get_matchups(1).json()["defense"]
        self.assertEqual(multipliers(defense["resist"])["grass"], 0.25)

    def test_offense_immunity_and_empty_groups(self):
        offense = self.get_matchups(2).json()["offense"]
        self.assertEqual(multipliers(offense["no_effect"]), {"ghost": 0})
        self.assertEqual(offense["strong"], [])

    def test_offense_uses_best_of_own_types_against_single_type(self):
        offense = self.get_matchups(3).json()["offense"]
        strong = multipliers(offense["strong"])
        self.assertEqual(strong["normal"], 2)
        self.assertEqual(strong["grass"], 2)
        self.assertEqual(offense["no_effect"], [])

    def test_every_type_is_returned_once_per_side(self):
        row = self.get_matchups().json()
        for side in ("defense", "offense"):
            entries = [entry for group in row[side].values() for entry in group]
            self.assertEqual(len(entries), 17)
            self.assertEqual({entry["type"] for entry in entries}, set(TYPES))

    def test_unknown_id_returns_404_without_calculation(self):
        with patch("api.services.pokemon_service.get_pokemon_matchups") as calculate:
            response = self.get_matchups(999)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "존재하지 않는 포켓몬입니다.")
        calculate.assert_not_called()

    def test_invalid_id_returns_422_before_loading_data(self):
        for value in (-1, "invalid", "1.5"):
            with self.subTest(value=value):
                response = self.get_matchups(value)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["detail"][0]["loc"], ["path", "pokemon_id"])
        self.loader.assert_not_called()

    def test_invalid_database_types_return_500_before_calculation(self):
        invalid = [None, "water", [], ["fairy"], ["water", "water"], [None],
                   ["water", []], ["water", "ground", "fire"]]
        with patch("api.services.pokemon_service.get_pokemon_matchups") as calculate:
            for types in invalid:
                with self.subTest(types=types):
                    self.pokemon[0]["types"] = types
                    response = self.get_matchups()
                    self.assertEqual(response.status_code, 500)
                    self.assertEqual(response.json()["detail"], "타입 상성 계산에 필요한 데이터가 올바르지 않습니다.")
        calculate.assert_not_called()

    def test_missing_types_return_500(self):
        del self.pokemon[0]["types"]
        self.assertEqual(self.get_matchups().status_code, 500)

    def test_read_failure_returns_500(self):
        self.loader.side_effect = OSError("read failed")
        self.assertEqual(self.get_matchups().status_code, 500)

    def test_does_not_depend_on_evolution_or_trainer_data(self):
        with patch("api.services.pokemon_service.get_pokemon_detail", side_effect=OSError), \
             patch("api.services.trainer_service.get_trainer", side_effect=OSError):
            self.assertEqual(self.get_matchups().status_code, 200)

    def test_openapi_documents_input_fields_and_error_responses(self):
        schema = self.client.get("/openapi.json").json()
        operation = schema["paths"]["/api/pokemon/{pokemon_id}/type-matchups"]["get"]
        self.assertEqual(operation["summary"], "포켓몬 타입별 공격·방어 상성 조회")
        self.assertEqual([p["name"] for p in operation["parameters"]], ["pokemon_id"])
        self.assertLessEqual({"200", "404", "422", "500"}, set(operation["responses"]))
        for name in ("PokemonTypeMatchups", "DefenseTypeMatchups", "OffenseTypeMatchups", "TypeMultiplier"):
            for field in schema["components"]["schemas"][name]["properties"].values():
                self.assertTrue(field["description"])


class RealPokemonTypeMatchupsApiTest(unittest.TestCase):
    def test_all_registered_pokemon_return_all_seventeen_types(self):
        with TestClient(app) as client:
            cards = client.get("/api/pokemon").json()
            self.assertTrue(cards)
            for card in cards:
                with self.subTest(pokemon_id=card["id"]):
                    response = client.get(f"/api/pokemon/{card['id']}/type-matchups")
                    self.assertEqual(response.status_code, 200)
                    row = response.json()
                    self.assertEqual(row["types"], card["types"])
                    for side in ("defense", "offense"):
                        entries = [entry for group in row[side].values() for entry in group]
                        self.assertEqual(len(entries), 17)
                        self.assertEqual({entry["type"] for entry in entries}, set(TYPES))
