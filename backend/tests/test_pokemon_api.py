import unittest
from typing import get_args
from unicodedata import normalize
from unittest.mock import patch

from fastapi.testclient import TestClient

from algorithm.type_chart import TYPES
from api.main import app
from api.schemas.pokemon import PokemonType


class PokemonSearchApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.pokemon = [
            {"id": 0, "name": "비크티니", "types": ["psychic", "fire"],
             "location_ids": [0], "usable": 0},
            {"id": 1, "name": "주리비얀", "types": ["grass"], "base_stat_total": 308},
            {"id": 4, "name": "뚜꾸리", "types": ["fire"]},
            {"id": 42, "name": "두까비", "types": ["water", "ground"]},
        ]
        loader = patch("api.services.pokemon_service._load_pokemon", return_value=self.pokemon)
        self.loader = loader.start()
        self.addCleanup(loader.stop)

    def get_results(self, params=None):
        response = self.client.get("/api/pokemon", params=params)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_without_filters_returns_all_cards_including_zero_id(self):
        rows = self.get_results()
        self.assertEqual([row["id"] for row in rows], [0, 1, 4, 42])
        self.assertEqual(rows[0], {
            "id": 0, "name": "비크티니", "types": ["psychic", "fire"], "image": None,
        })
        self.assertTrue(all(set(row) == {"id", "name", "types", "image"} for row in rows))

    def test_name_only_matches_partial_name(self):
        self.assertEqual([row["id"] for row in self.get_results({"name": "주리"})], [1])

    def test_type_only_includes_both_primary_and_secondary_types(self):
        self.assertEqual([row["id"] for row in self.get_results({"type": "fire"})], [0, 4])
        self.assertEqual([row["id"] for row in self.get_results({"type": "ground"})], [42])

    def test_combined_filters_require_both_conditions(self):
        rows = self.get_results({"name": "비", "type": "fire"})
        self.assertEqual([row["id"] for row in rows], [0])

    def test_no_matching_name_returns_empty_list(self):
        self.assertEqual(self.get_results({"name": "없는포켓몬"}), [])

    def test_conflicting_filters_return_empty_list(self):
        self.assertEqual(self.get_results({"name": "주리", "type": "fire"}), [])

    def test_empty_and_whitespace_name_do_not_filter(self):
        for name in ("", "   "):
            with self.subTest(name=name):
                self.assertEqual(len(self.get_results({"name": name})), 4)
        self.assertEqual([r["id"] for r in self.get_results({"name": "  주리  "})], [1])

    def test_decomposed_korean_name_matches(self):
        rows = self.get_results({"name": normalize("NFD", "주리")})
        self.assertEqual([row["id"] for row in rows], [1])

    def test_invalid_types_return_422_before_loading_data(self):
        for pokemon_type in ("fairy", "invalid", "풀", ""):
            with self.subTest(pokemon_type=pokemon_type):
                response = self.client.get("/api/pokemon", params={"type": pokemon_type})
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["detail"][0]["loc"], ["query", "type"])
        self.loader.assert_not_called()

    def test_empty_dataset_returns_empty_list(self):
        self.loader.return_value = []
        self.assertEqual(self.get_results(), [])

    def test_image_from_data_is_preserved(self):
        self.pokemon[1]["image"] = "/images/example.png"
        self.assertEqual(self.get_results({"name": "주리"})[0]["image"], "/images/example.png")

    def test_allowed_types_match_generation_five_algorithm(self):
        self.assertEqual(set(get_args(PokemonType)), set(TYPES))
