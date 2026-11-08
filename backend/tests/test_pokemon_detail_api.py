import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app


class PokemonDetailApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.pokemon = [
            {"id": 0, "name": "예시 단독", "types": ["psychic"], "base_stat_total": 600,
             "location_ids": [1], "evolution": None, "usable": 0},
            {"id": 1, "name": "예시 기본", "types": ["grass"], "base_stat_total": 300},
            {"id": 2, "name": "예시 중간", "types": ["grass"], "base_stat_total": 400},
            {"id": 3, "name": "예시 최종", "types": ["grass"], "base_stat_total": 500},
            {"id": 4, "name": "예시 미등록", "types": ["fire"], "base_stat_total": 300,
             "evolution": None},
            {"id": 5, "name": "예시 분기", "types": ["water"], "base_stat_total": 450},
            {"id": 6, "name": "다른 계보 기본", "types": ["normal"], "base_stat_total": 300},
            {"id": 7, "name": "다른 계보 최종", "types": ["normal"], "base_stat_total": 400},
        ]
        self.evolutions = {
            "relations": [
                {"from_pokemon_id": 1, "to_pokemon_id": 2, "condition": "레벨 17"},
                {"from_pokemon_id": 2, "to_pokemon_id": 3, "condition": "레벨 36"},
                {"from_pokemon_id": 6, "to_pokemon_id": 7, "condition": "예시 조건"},
            ],
            "no_evolution_pokemon_ids": [0],
        }
        loader = patch("api.services.pokemon_service._load_pokemon", return_value=self.pokemon)
        loader.start()
        self.addCleanup(loader.stop)
        evolutions = patch("api.services.pokemon_service._load_evolutions", return_value=self.evolutions)
        self.evolution_loader = evolutions.start()
        self.addCleanup(evolutions.stop)

    def get_detail(self, pokemon_id):
        response = self.client.get(f"/api/pokemon/{pokemon_id}")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_detail_contains_only_public_fields_and_default_image(self):
        row = self.get_detail(0)
        self.assertEqual(row, {
            "id": 0, "name": "예시 단독", "types": ["psychic"], "image": None,
            "base_stat_total": 600, "evolution_chain": [],
        })

    def test_any_stage_returns_the_same_complete_chain(self):
        expected = [
            {"from": {"id": 1, "name": "예시 기본"},
             "to": {"id": 2, "name": "예시 중간"}, "condition": "레벨 17"},
            {"from": {"id": 2, "name": "예시 중간"},
             "to": {"id": 3, "name": "예시 최종"}, "condition": "레벨 36"},
        ]
        for pokemon_id in (1, 2, 3):
            with self.subTest(pokemon_id=pokemon_id):
                row = self.get_detail(pokemon_id)
                self.assertEqual(row["id"], pokemon_id)
                self.assertEqual(row["evolution_chain"], expected)

    def test_branch_leaf_includes_sibling_branch(self):
        self.evolutions["relations"].append({
            "from_pokemon_id": 1, "to_pokemon_id": 5, "condition": "예시 분기 조건",
        })
        for pokemon_id in (1, 3, 5):
            with self.subTest(pokemon_id=pokemon_id):
                chain = self.get_detail(pokemon_id)["evolution_chain"]
                self.assertEqual([(r["from"]["id"], r["to"]["id"]) for r in chain],
                                 [(1, 2), (2, 3), (1, 5)])
                self.assertEqual(chain[-1]["condition"], "예시 분기 조건")

    def test_unregistered_evolution_is_null_even_when_original_condition_is_null(self):
        self.assertIsNone(self.get_detail(4)["evolution_chain"])

    def test_known_no_evolution_is_empty_array(self):
        self.assertEqual(self.get_detail(0)["evolution_chain"], [])

    def test_image_is_preserved(self):
        self.pokemon[2]["image"] = "/images/example.png"
        self.assertEqual(self.get_detail(2)["image"], "/images/example.png")

    def test_unknown_id_returns_404_without_loading_evolution(self):
        response = self.client.get("/api/pokemon/999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "존재하지 않는 포켓몬입니다.")
        self.evolution_loader.assert_not_called()

    def test_non_numeric_id_returns_422(self):
        response = self.client.get("/api/pokemon/invalid")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"][0]["loc"], ["path", "pokemon_id"])
        self.evolution_loader.assert_not_called()

    def test_search_response_does_not_include_detail_fields(self):
        response = self.client.get("/api/pokemon", params={"name": "예시 중간"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{
            "id": 2, "name": "예시 중간", "types": ["grass"], "image": None,
        }])
        self.evolution_loader.assert_not_called()
