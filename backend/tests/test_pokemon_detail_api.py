from copy import deepcopy
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
        self.pokemon[0].update(evolution_from=None, evolution_to=None)
        self.pokemon[1].update(evolution_from=None, evolution_to=[
            {"id": 2, "condition": "17"},
        ])
        self.pokemon[2].update(
            evolution_from=[{"id": 1, "condition": "17"}],
            evolution_to=[{"id": 3, "condition": "36"}],
        )
        self.pokemon[3].update(evolution_from=[{"id": 2, "condition": "36"}], evolution_to=None)
        self.pokemon[5].update(evolution_from=None, evolution_to=None)
        self.pokemon[6].update(evolution_from=None, evolution_to=[{"id": 7, "condition": "예시 조건"}])
        self.pokemon[7].update(evolution_from=[{"id": 6, "condition": "예시 조건"}], evolution_to=None)
        loader = patch("api.services.pokemon_service._load_pokemon", return_value=self.pokemon)
        self.pokemon_loader = loader.start()
        self.addCleanup(loader.stop)

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
        self.pokemon[1]["evolution_to"].append({"id": 5, "condition": "예시 분기 조건"})
        self.pokemon[5]["evolution_from"] = [{"id": 1, "condition": "예시 분기 조건"}]
        for pokemon_id in (1, 3, 5):
            with self.subTest(pokemon_id=pokemon_id):
                chain = self.get_detail(pokemon_id)["evolution_chain"]
                self.assertEqual([(r["from"]["id"], r["to"]["id"]) for r in chain],
                                 [(1, 2), (1, 5), (2, 3)])
                self.assertEqual(chain[1]["condition"], "예시 분기 조건")

    def test_unregistered_evolution_is_null(self):
        self.assertIsNone(self.get_detail(4)["evolution_chain"])

    def test_known_no_evolution_is_empty_array(self):
        self.assertEqual(self.get_detail(0)["evolution_chain"], [])

    def test_image_is_preserved(self):
        self.pokemon[2]["image"] = "/images/example.png"
        self.assertEqual(self.get_detail(2)["image"], "/images/example.png")

    def test_unknown_id_returns_404(self):
        response = self.client.get("/api/pokemon/999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "존재하지 않는 포켓몬입니다.")

    def test_non_numeric_id_returns_422(self):
        response = self.client.get("/api/pokemon/invalid")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"][0]["loc"], ["path", "pokemon_id"])

    def test_search_response_does_not_include_detail_fields(self):
        response = self.client.get("/api/pokemon", params={"name": "예시 중간"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{
            "id": 2, "name": "예시 중간", "types": ["grass"], "image": None,
        }])


    def test_relationship_is_read_from_either_side_and_not_duplicated(self):
        # 진화 후 포켓몬 쪽에만 등록되어 있어도 기본 단계에서 전체 계보를 조회합니다.
        self.pokemon[1]["evolution_to"] = None
        self.pokemon[2]["evolution_to"] = None
        chain = self.get_detail(1)["evolution_chain"]
        self.assertEqual([(r["from"]["id"], r["to"]["id"]) for r in chain], [(1, 2), (2, 3)])

    def test_non_level_conditions_are_preserved(self):
        for condition in ("리프의돌", "통신", "친밀도"):
            with self.subTest(condition=condition):
                self.pokemon[1]["evolution_to"][0]["condition"] = condition
                self.pokemon[2]["evolution_from"][0]["condition"] = condition
                self.assertEqual(self.get_detail(1)["evolution_chain"][0]["condition"], condition)

    def test_zero_id_can_be_an_evolution_reference(self):
        self.pokemon[0]["evolution_to"] = [{"id": 5, "condition": "예시 조건"}]
        chain = self.get_detail(5)["evolution_chain"]
        self.assertEqual(chain[0]["from"]["id"], 0)

    def test_partial_registration_is_not_reported_as_no_evolution(self):
        self.pokemon[4]["evolution_from"] = None
        self.assertIsNone(self.get_detail(4)["evolution_chain"])

    def test_broken_evolution_data_returns_500(self):
        original = deepcopy(self.pokemon)
        cases = [
            ("missing pokemon", [{"id": 999, "condition": "17"}]),
            ("invalid id", [{"id": True, "condition": "17"}]),
            ("missing condition", [{"id": 2}]),
            ("blank condition", [{"id": 2, "condition": " "}]),
            ("invalid relation", [None]),
            ("invalid list", {}),
            ("self reference", [{"id": 1, "condition": "17"}]),
            ("conflicting condition", [{"id": 2, "condition": "99"}]),
        ]
        with TestClient(app, raise_server_exceptions=False) as client:
            for label, entries in cases:
                with self.subTest(case=label):
                    self.pokemon[:] = deepcopy(original)
                    self.pokemon[1]["evolution_to"] = entries
                    response = client.get("/api/pokemon/1")
                    self.assertEqual(response.status_code, 500)

    def test_unrelated_broken_evolution_does_not_block_valid_details(self):
        original = deepcopy(self.pokemon)
        cases = [
            [{"id": 999, "condition": "17"}],
            [{"id": True, "condition": "17"}],
            [{"id": 7}],
            [{"id": 7, "condition": " "}],
            [None],
            {},
            [{"id": 6, "condition": "17"}],
            [{"id": 7, "condition": "충돌하는 조건"}],
        ]
        expected = self.get_detail(1)["evolution_chain"]
        with TestClient(app, raise_server_exceptions=False) as client:
            for entries in cases:
                with self.subTest(entries=entries):
                    self.pokemon[:] = deepcopy(original)
                    self.pokemon[6]["evolution_to"] = entries
                    for pokemon_id in (1, 2, 3):
                        self.assertEqual(self.get_detail(pokemon_id)["evolution_chain"], expected)
                    self.assertEqual(self.get_detail(0)["evolution_chain"], [])
                    self.assertIsNone(self.get_detail(4)["evolution_chain"])
                    self.assertEqual(client.get("/api/pokemon/6").status_code, 500)

    def test_connected_broken_evolution_blocks_every_stage(self):
        self.pokemon[3]["evolution_to"] = [{"id": 999, "condition": "50"}]
        with TestClient(app, raise_server_exceptions=False) as client:
            for pokemon_id in (1, 2, 3):
                with self.subTest(pokemon_id=pokemon_id):
                    self.assertEqual(client.get(f"/api/pokemon/{pokemon_id}").status_code, 500)

    def test_unknown_id_does_not_parse_evolution_data(self):
        self.pokemon[1]["evolution_to"] = "잘못된 데이터"
        response = self.client.get("/api/pokemon/999")
        self.assertEqual(response.status_code, 404)


class RealPokemonEvolutionApiTest(unittest.TestCase):
    def test_real_evolution_chains_and_conditions(self):
        with TestClient(app) as client:
            expected = [
                {"from": {"id": 35, "name": "두더류"},
                 "to": {"id": 36, "name": "몰드류"}, "condition": "레벨 31"},
            ]
            for pokemon_id in (35, 36):
                with self.subTest(pokemon_id=pokemon_id):
                    response = client.get(f"/api/pokemon/{pokemon_id}")
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json()["evolution_chain"], expected)
            self.assertEqual(client.get("/api/pokemon/17").json()["evolution_chain"][0]["condition"], "리프의돌")
            self.assertEqual(client.get("/api/pokemon/0").json()["evolution_chain"], [])

    def test_every_registered_pokemon_has_registered_evolution_information(self):
        with TestClient(app) as client:
            cards = client.get("/api/pokemon").json()
            self.assertTrue(cards)
            for card in cards:
                with self.subTest(pokemon_id=card["id"]):
                    response = client.get(f"/api/pokemon/{card['id']}")
                    self.assertEqual(response.status_code, 200)
                    self.assertIsNotNone(response.json()["evolution_chain"])
