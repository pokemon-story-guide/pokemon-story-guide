import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from api.services import trainer_service


class TrainerRecommendationsApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.pokemon = [
            {"id": 9, "name": "물 후보", "types": ["water"]},
            {"id": 2, "name": "땅 후보 둘", "types": ["ground"]},
            {"id": 0, "name": "땅 후보 하나", "types": ["ground"]},
            {"id": 29, "name": "전기 상대", "types": ["electric"]},
        ]
        self.trainer = {
            "id": "elesa", "name": "카밀레",
            "party": [{"pokemon_id": 29, "level": 27}],
        }
        loader = patch("api.services.pokemon_service._load_pokemon", return_value=self.pokemon)
        self.loader = loader.start()
        self.addCleanup(loader.stop)
        trainer = patch("api.services.trainer_service.get_trainer", return_value=self.trainer)
        self.get_trainer = trainer.start()
        self.addCleanup(trainer.stop)

    def request(self, trainer_id="elesa", **params):
        return self.client.get(f"/api/recommendations/trainers/{trainer_id}", params=params)

    def assert_data_error(self):
        response = self.request()
        self.assertEqual(response.status_code, 500, response.text)
        self.assertEqual(response.json()["detail"], "추천 계산에 필요한 데이터가 올바르지 않습니다.")

    def test_score_sort_and_id_tie_break_with_zero_id(self):
        response = self.request()
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual((data["trainer_id"], data["trainer_name"], data["total_count"]), ("elesa", "카밀레", 4))
        self.assertEqual([item["pokemon_id"] for item in data["items"]], [0, 2, 29, 9])
        self.assertEqual([item["score"] for item in data["items"]], [88, 88, 50, 38])
        self.assertEqual(data["items"][0]["rating"], "good")
        self.assertEqual(data["items"][-1]["rating"], "bad")
        self.assertIn("포획 가능 여부는 반영하지 않습니다", data["evaluation_basis"])
        self.assertIn("승률이 아닙니다", data["evaluation_basis"])

    def test_limit_does_not_change_total_count(self):
        response = self.request(limit=1)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()["items"]), 1)
        self.assertEqual(response.json()["total_count"], 4)
        self.assertEqual(response.json()["items"][0]["pokemon_id"], 0)

    def test_limit_larger_than_candidates_returns_available_candidates(self):
        response = self.request(limit=50)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()["items"]), 4)

    def test_default_limit_is_ten(self):
        self.pokemon[:] = [
            {"id": index, "name": f"후보 {index}", "types": ["electric"]}
            for index in range(30)
        ]
        response = self.request()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["total_count"], 30)
        self.assertEqual([item["pokemon_id"] for item in response.json()["items"]], list(range(10)))

    def test_reasons_and_warnings_match_existing_single_evaluation(self):
        data = self.request().json()
        for item in data["items"]:
            with self.subTest(pokemon_id=item["pokemon_id"]):
                single = self.client.get("/api/recommendations", params={
                    "pokemon_id": item["pokemon_id"], "trainer_id": "elesa",
                })
                self.assertEqual(single.status_code, 200, single.text)
                for key in ("score", "rating", "rating_label", "reasons", "warnings"):
                    self.assertEqual(item[key], single.json()[key])
        self.assertTrue(data["items"][0]["reasons"])
        self.assertTrue(data["items"][-1]["warnings"])

    def test_attack_immunity_and_defense_advantage_are_both_explained(self):
        self.pokemon.append({"id": 93, "name": "에몽가", "types": ["electric", "flying"]})
        self.trainer["party"].append({"pokemon_id": 93, "level": 25})
        response = self.request()
        self.assertEqual(response.status_code, 200, response.text)
        ground = next(item for item in response.json()["items"] if item["pokemon_id"] == 0)
        self.assertTrue(any("효과가 없습니다" in text for text in ground["warnings"]))
        self.assertTrue(any("효과가 없습니다" in text for text in ground["reasons"]))

    def test_unknown_trainer_returns_404(self):
        self.get_trainer.return_value = None
        response = self.request("missing")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "존재하지 않는 인물입니다.")
        self.loader.assert_not_called()

    def test_invalid_limits_return_422_before_loading(self):
        for limit in (0, -1, 51, "abc", "1.5", ""):
            with self.subTest(limit=limit):
                self.assertEqual(self.request(limit=limit).status_code, 422)
        self.get_trainer.assert_not_called()
        self.loader.assert_not_called()

    def test_whitespace_trainer_id_returns_422_before_loading(self):
        for trainer_id in ("%20", "el%20esa"):
            self.assertEqual(self.request(trainer_id).status_code, 422)
        self.get_trainer.assert_not_called()

    def test_empty_party_returns_500(self):
        self.trainer["party"] = []
        self.assert_data_error()

    def test_missing_party_reference_returns_500(self):
        self.trainer["party"][0]["pokemon_id"] = 999
        self.assert_data_error()

    def test_invalid_candidate_is_not_silently_skipped_even_outside_limit(self):
        for types in ([], ["fairy"], ["water", "water"], "water", None):
            with self.subTest(types=types):
                self.pokemon[0]["types"] = types
                self.assertEqual(self.request(limit=1).status_code, 500)

    def test_duplicate_and_invalid_candidate_ids_return_500(self):
        for pokemon_id in (2, -1, True, "9", None):
            with self.subTest(pokemon_id=pokemon_id):
                self.pokemon[0]["id"] = pokemon_id
                self.assert_data_error()

    def test_invalid_name_returns_500(self):
        self.pokemon[0]["name"] = " "
        self.assert_data_error()

    def test_data_read_failure_returns_500(self):
        self.loader.side_effect = OSError("test failure")
        self.assert_data_error()

    def test_openapi_describes_parameters_and_response_fields(self):
        schema = self.client.get("/openapi.json").json()
        operation = schema["paths"]["/api/recommendations/trainers/{trainer_id}"]["get"]
        self.assertEqual({p["name"] for p in operation["parameters"]}, {"trainer_id", "limit"})
        self.assertTrue(all(p.get("description") for p in operation["parameters"]))
        for model in ("TrainerRecommendations", "TrainerRecommendationItem"):
            fields = schema["components"]["schemas"][model]["properties"]
            self.assertTrue(all(field.get("description") for field in fields.values()))


class RealTrainerRecommendationsApiTest(unittest.TestCase):
    def test_all_registered_trainers_return_sorted_candidates_and_matching_evaluations(self):
        with TestClient(app) as client:
            trainers = trainer_service.get_trainers()
            self.assertTrue(trainers)
            for trainer in trainers:
                with self.subTest(trainer_id=trainer["id"]):
                    response = client.get(f"/api/recommendations/trainers/{trainer['id']}")
                    self.assertEqual(response.status_code, 200, response.text)
                    data = response.json()
                    self.assertEqual(data["trainer_name"], trainer["name"])
                    self.assertEqual(data["total_count"], 156)
                    self.assertEqual(len(data["items"]), 10)
                    keys = [(-item["score"], item["pokemon_id"]) for item in data["items"]]
                    self.assertEqual(keys, sorted(keys))
                    self.assertEqual(len({item["pokemon_id"] for item in data["items"]}), 10)
                    item = data["items"][0]
                    single = client.get("/api/recommendations", params={
                        "pokemon_id": item["pokemon_id"], "trainer_id": trainer["id"],
                    })
                    self.assertEqual(single.status_code, 200, single.text)
                    for key in ("score", "rating", "rating_label", "reasons", "warnings"):
                        self.assertEqual(item[key], single.json()[key])


if __name__ == "__main__":
    unittest.main()
