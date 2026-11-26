import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from algorithm.overall import evaluate_overall
from api.main import app
from api.services import pokemon_service, trainer_service


class OverallRecommendationApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.pokemon = [
            {"id": 0, "name": "물 후보", "types": ["water"]},
            {"id": 1, "name": "불 상대", "types": ["fire"]},
            {"id": 2, "name": "풀 상대", "types": ["grass"]},
            {"id": 3, "name": "전기 상대", "types": ["electric"]},
        ]
        self.trainers = [
            self.trainer("chili", "팟", "gym-leader", 1, badge=1),
            self.trainer("cilan", "덴트", "gym-leader", 2, badge=1),
            self.trainer("cress", "콘", "gym-leader", 0, badge=1),
            self.trainer("elesa", "카밀레", "gym-leader", 3, badge=4),
            self.trainer("shauntal", "망초", "elite-four", 2),
            self.trainer("alder", "노간주", "champion", 1),
            self.trainer("ghetsis", "게치스", "plasma", 2),
            self.trainer("n-accumula-town", "N", "plasma", 3),
        ]
        loader = patch("api.services.pokemon_service._load_pokemon", return_value=self.pokemon)
        self.loader = loader.start()
        self.addCleanup(loader.stop)
        trainers = patch("api.services.trainer_service.get_trainers", return_value=self.trainers)
        self.get_trainers = trainers.start()
        self.addCleanup(trainers.stop)

    @staticmethod
    def trainer(trainer_id, name, category, pokemon_id, badge=None):
        return {
            "id": trainer_id, "name": name, "category": category,
            "badge_order": badge, "party": [{"pokemon_id": pokemon_id, "level": 20}],
        }

    def request(self, pokemon_id=0):
        return self.client.get(f"/api/pokemon/{pokemon_id}/overall-recommendation")

    def assert_data_error(self):
        response = self.request()
        self.assertEqual(response.status_code, 500, response.text)
        self.assertEqual(response.json()["detail"], "전체 추천도 계산에 필요한 데이터가 올바르지 않습니다.")

    def enriched_opponents(self):
        by_id = {row["id"]: row for row in self.pokemon}
        return [
            {**trainer, "party": [
                {**member, "types": by_id[member["pokemon_id"]]["types"]}
                for member in trainer["party"]
            ]}
            for trainer in self.trainers
        ]

    def test_group_average_is_not_individual_trainer_average(self):
        response = self.request()
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual((data["pokemon_id"], data["name"], data["types"]), (0, "물 후보", ["water"]))
        # 체육관 1: (75+25+50)/3=50, 나머지는 38, 25, 75, 25 -> 전체 43.
        self.assertEqual((data["score"], data["rating"], data["rating_label"]), (43, "normal", "보통"))
        groups = {detail["group"]: detail for detail in data["details"]}
        self.assertEqual(groups["gym-1"]["score"], 50)
        self.assertEqual(len(groups["gym-1"]["opponents"]), 3)
        self.assertEqual(groups["gym-1"]["group_name"], "1번째 체육관")
        self.assertEqual(data["summary"], {
            "group_count": 5, "good_count": 1, "bad_count": 3,
            "best_group": "alder", "worst_group": "shauntal",
        })
        self.assertTrue(all(group["weight"] == 1 for group in data["details"]))

    def test_ghetsis_included_and_n_excluded(self):
        data = self.request().json()
        ids = {opponent["id"] for group in data["details"] for opponent in group["opponents"]}
        self.assertIn("ghetsis", ids)
        self.assertNotIn("n-accumula-town", ids)
        self.assertIn("N은 제외", data["evaluation_basis"])

    def test_excluded_n_party_does_not_affect_evaluation(self):
        before = self.request().json()
        self.trainers[-1]["party"] = [{"pokemon_id": 999}]
        response = self.request()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), before)

    def test_scores_and_summary_match_existing_algorithm(self):
        expected = evaluate_overall(["water"], self.enriched_opponents())
        data = self.request().json()
        for key in ("score", "rating", "rating_label", "summary"):
            self.assertEqual(data[key], expected[key])
        for actual, original in zip(data["details"], expected["details"], strict=True):
            for key in ("group", "category", "score", "weight"):
                self.assertEqual(actual[key], original[key])
            for actual_opponent, original_opponent in zip(actual["opponents"], original["opponents"], strict=True):
                for key in ("id", "name", "score", "rating"):
                    self.assertEqual(actual_opponent[key], original_opponent[key])

    def test_explanation_uses_computed_names_scores_and_scope(self):
        data = self.request().json()
        self.assertIn("5개 그룹", data["explanation"])
        self.assertIn("43점(보통)", data["explanation"])
        self.assertIn("최고 점수 그룹은 노간주(75점)", data["explanation"])
        self.assertIn("최저 점수 그룹은 망초(25점)", data["explanation"])
        self.assertIn("최고 점수도 유리한 상성이나 승리를 보장하지 않습니다", data["explanation"])
        self.assertIn("실제 기술·특성·능력치·레벨은 반영하지 않습니다", data["evaluation_basis"])
        self.assertIn("포획 가능 여부는 반영하지 않습니다", data["evaluation_basis"])

    def test_all_neutral_groups_keep_original_tie_behavior(self):
        for pokemon in self.pokemon:
            pokemon["types"] = ["normal"]
        data = self.request().json()
        self.assertEqual(data["score"], 50)
        self.assertEqual(data["summary"]["best_group"], "ghetsis")
        self.assertEqual(data["summary"]["worst_group"], "gym-1")

    def test_unknown_pokemon_returns_404_without_loading_trainers(self):
        response = self.request(999)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "존재하지 않는 포켓몬입니다.")
        self.get_trainers.assert_not_called()

    def test_invalid_ids_return_422_before_loading_data(self):
        for pokemon_id in (-1, "abc", "1.5"):
            with self.subTest(pokemon_id=pokemon_id):
                self.assertEqual(self.request(pokemon_id).status_code, 422)
        self.loader.assert_not_called()
        self.get_trainers.assert_not_called()

    def test_missing_party_reference_returns_500(self):
        self.trainers[0]["party"][0]["pokemon_id"] = 999
        self.assert_data_error()

    def test_empty_included_party_returns_500(self):
        self.trainers[0]["party"] = []
        self.assert_data_error()

    def test_no_eligible_opponents_returns_500(self):
        self.trainers[:] = [self.trainers[-1]]
        self.assert_data_error()

    def test_invalid_selected_types_return_500(self):
        for types in (None, [], "water", ["fairy"], ["water", "water"]):
            with self.subTest(types=types):
                self.pokemon[0]["types"] = types
                self.assert_data_error()

    def test_invalid_opponent_types_return_500(self):
        self.pokemon[1]["types"] = []
        self.assert_data_error()

    def test_duplicate_pokemon_id_returns_500(self):
        self.pokemon[1]["id"] = 0
        self.assert_data_error()

    def test_duplicate_trainer_id_returns_500(self):
        self.trainers[1]["id"] = self.trainers[0]["id"]
        self.assert_data_error()

    def test_invalid_badge_order_returns_500(self):
        for badge in (True, 0, -1, "1"):
            with self.subTest(badge=badge):
                self.trainers[0]["badge_order"] = badge
                self.assert_data_error()

    def test_invalid_trainer_name_returns_500(self):
        self.trainers[0]["name"] = " "
        self.assert_data_error()

    def test_data_read_failure_returns_500(self):
        self.get_trainers.side_effect = OSError("test failure")
        self.assert_data_error()

    def test_openapi_describes_id_and_all_response_fields(self):
        schema = self.client.get("/openapi.json").json()
        operation = schema["paths"]["/api/pokemon/{pokemon_id}/overall-recommendation"]["get"]
        self.assertEqual(operation["parameters"][0]["name"], "pokemon_id")
        self.assertTrue(operation["parameters"][0]["description"])
        self.assertTrue({"404", "422", "500"} <= set(operation["responses"]))
        for model in ("OverallRecommendation", "OverallRecommendationSummary", "OverallGroupEvaluation", "OverallOpponentEvaluation"):
            self.assertTrue(all(field.get("description") for field in schema["components"]["schemas"][model]["properties"].values()))


class RealOverallRecommendationApiTest(unittest.TestCase):
    def test_all_registered_pokemon_match_real_overall_algorithm(self):
        pokemon = pokemon_service.search_pokemon()
        by_id = {row["id"]: row for row in pokemon}
        opponents = [
            {**trainer, "party": [
                {**member, "types": by_id[member["pokemon_id"]]["types"]}
                for member in trainer["party"]
            ]}
            for trainer in trainer_service.get_trainers()
        ]
        with TestClient(app) as client:
            self.assertTrue(pokemon)
            for row in pokemon:
                with self.subTest(pokemon_id=row["id"]):
                    response = client.get(f"/api/pokemon/{row['id']}/overall-recommendation")
                    self.assertEqual(response.status_code, 200, response.text)
                    data = response.json()
                    expected = evaluate_overall(row["types"], opponents)
                    for key in ("score", "rating", "rating_label", "summary"):
                        self.assertEqual(data[key], expected[key])
                    self.assertEqual(data["summary"]["group_count"], 14)
                    group_ids = {detail["group"] for detail in data["details"]}
                    self.assertIn(data["summary"]["best_group"], group_ids)
                    self.assertIn(data["summary"]["worst_group"], group_ids)
                    ids = {opponent["id"] for group in data["details"] for opponent in group["opponents"]}
                    self.assertIn("ghetsis", ids)
                    self.assertFalse(any(trainer_id.startswith("n-") for trainer_id in ids))


if __name__ == "__main__":
    unittest.main()
