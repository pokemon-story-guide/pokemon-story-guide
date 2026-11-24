import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app


class PokemonTrainerEvaluationsApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.pokemon = [
            {"id": 35, "name": "두더류", "types": ["ground"]},
            {"id": 93, "name": "에몽가", "types": ["electric", "flying"]},
            {"id": 29, "name": "제브라이카", "types": ["electric"]},
            {"id": 2, "name": "예시 포켓몬", "types": ["ghost"]},
        ]
        self.trainers = [
            {"id": "leader-a", "name": "예시 관장", "category": "gym-leader", "type": "electric",
             "badge_order": 1, "image": "",
             "party": [{"pokemon_id": 93, "level": 25}, {"pokemon_id": 29, "level": 27}]},
            {"id": "elite-a", "name": "예시 사천왕", "category": "elite-four", "type": "ghost",
             "badge_order": None, "image": "", "party": [{"pokemon_id": 2, "level": 50}]},
        ]
        for target, value in (
            ("api.services.pokemon_service._load_pokemon", self.pokemon),
            ("api.services.trainer_service._load_data", self.trainers),
        ):
            mocker = patch(target, return_value=value)
            mocker.start()
            self.addCleanup(mocker.stop)

    def test_returns_every_trainer_in_list_order(self):
        response = self.client.get("/api/recommendations/pokemon/35")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["name"], "두더류")
        self.assertEqual([item["trainer_id"] for item in body["items"]], ["leader-a", "elite-a"])
        self.assertEqual([item["badge_order"] for item in body["items"]], [1, None])

    def test_category_filter(self):
        response = self.client.get("/api/recommendations/pokemon/35", params={"category": "gym-leader"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["trainer_id"] for item in response.json()["items"]], ["leader-a"])

    def test_each_item_matches_single_recommendation_api(self):
        items = self.client.get("/api/recommendations/pokemon/35").json()["items"]
        for item in items:
            with self.subTest(trainer_id=item["trainer_id"]):
                single = self.client.get(
                    "/api/recommendations",
                    params={"pokemon_id": 35, "trainer_id": item["trainer_id"]},
                ).json()
                for key in ("score", "rating", "rating_label", "reasons", "warnings"):
                    self.assertEqual(item[key], single[key])

    def test_unknown_pokemon_returns_404(self):
        response = self.client.get("/api/recommendations/pokemon/999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "존재하지 않는 포켓몬입니다.")

    def test_invalid_requests_return_422(self):
        for path in ("/api/recommendations/pokemon/-1", "/api/recommendations/pokemon/35?category=river"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 422)

    def test_party_with_unknown_pokemon_returns_500(self):
        self.trainers[0]["party"] = [{"pokemon_id": 999, "level": 10}]
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/api/recommendations/pokemon/35")
        self.assertEqual(response.status_code, 500)