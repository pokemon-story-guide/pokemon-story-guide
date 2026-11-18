import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from api.services.recommendation_explanation import build_explanation


class RecommendationExplanationTest(unittest.TestCase):
    def explain(self, *, offense=1, defense=1, attack="water", threat="fire", count=1):
        detail = {
            "pokemon_id": 1, "name": "상대 포켓몬",
            "best_attack_type": attack, "offense_multiplier": offense,
            "threat_type": threat, "defense_multiplier": defense,
        }
        return build_explanation({"details": [detail.copy() for _ in range(count)]})

    def test_four_times_advantage_keeps_defense_warning(self):
        result = self.explain(offense=4, defense=2, threat="grass")
        self.assertEqual(result["reasons"], ["물 타입 공격은 상대 포켓몬에게 4배의 효과가 있습니다."])
        self.assertEqual(result["warnings"], ["상대 포켓몬의 풀 타입 공격은 이 포켓몬에게 2배의 효과가 있어 주의가 필요합니다."])

    def test_attack_immunity_is_not_described_as_resistance(self):
        result = self.explain(offense=0, attack="ground", threat="flying")
        self.assertEqual(result["reasons"], [])
        self.assertEqual(result["warnings"], ["땅 타입 공격은 상대 포켓몬에게 효과가 없습니다."])

    def test_quarter_resistance_and_defense_immunity(self):
        result = self.explain(offense=0.25, defense=0, threat="electric")
        self.assertEqual(result["warnings"], ["물 타입 공격은 상대 포켓몬에게 0.25배의 효과만 있습니다."])
        self.assertEqual(result["reasons"], ["상대 포켓몬의 전기 타입 공격은 이 포켓몬에게 효과가 없습니다."])

    def test_defense_resistance(self):
        for multiplier in (0.5, 0.25):
            with self.subTest(multiplier=multiplier):
                self.assertEqual(self.explain(defense=multiplier)["reasons"], [
                    f"상대 포켓몬의 불꽃 타입 공격은 이 포켓몬에게 {multiplier:g}배의 효과만 있습니다."
                ])

    def test_neutral_explains_no_type_advantage(self):
        result = self.explain()
        self.assertEqual(result["reasons"], ["평가한 공격·방어 배율이 모두 1배로, 타입 상성에 따른 뚜렷한 이점이나 약점이 없습니다."])
        self.assertEqual(result["warnings"], [])

    def test_duplicate_members_are_counted_once_in_text(self):
        result = self.explain(offense=0, count=2)
        self.assertEqual(result["warnings"], ["물 타입 공격은 상대 포켓몬 2마리에게 효과가 없습니다."])


class RecommendationApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.pokemon = [
            {"id": 0, "name": "비크티니", "types": ["psychic", "fire"]},
            {"id": 35, "name": "두더류", "types": ["ground"]},
            {"id": 86, "name": "꼬지보리", "types": ["water", "flying"]},
            {"id": 93, "name": "에몽가", "types": ["electric", "flying"]},
            {"id": 29, "name": "제브라이카", "types": ["electric"]},
        ]
        self.trainer = {
            "id": "elesa", "name": "카밀레", "party": [
                {"pokemon_id": 93, "level": 25},
                {"pokemon_id": 93, "level": 25},
                {"pokemon_id": 29, "level": 27},
            ],
        }
        for target, value in (
            ("api.services.pokemon_service._load_pokemon", self.pokemon),
            ("api.services.trainer_service.get_trainer", self.trainer),
        ):
            mocker = patch(target, return_value=value)
            mocked = mocker.start()
            self.addCleanup(mocker.stop)
            if "get_trainer" in target:
                self.get_trainer = mocked
            else:
                self.load_pokemon = mocked

    def get_recommendation(self, pokemon_id=35, trainer_id="elesa"):
        return self.client.get("/api/recommendations", params={
            "pokemon_id": pokemon_id, "trainer_id": trainer_id,
        })

    def test_ground_against_elesa_returns_score_and_both_sides_of_explanation(self):
        response = self.get_recommendation()
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual((data["pokemon_id"], data["trainer_id"]), (35, "elesa"))
        self.assertEqual((data["score"], data["rating"], data["rating_label"]), (54, "normal", "보통"))
        self.assertEqual(data["reasons"], [
            "땅 타입 공격은 제브라이카에게 2배의 효과가 있습니다.",
            "제브라이카의 전기 타입 공격은 이 포켓몬에게 효과가 없습니다.",
        ])
        self.assertEqual(data["warnings"], ["땅 타입 공격은 에몽가 2마리에게 효과가 없습니다."])
        self.assertIn("실제 기술·특성·능력치·레벨은 반영하지 않습니다", data["evaluation_basis"])
        self.assertEqual(set(data), {
            "pokemon_id", "trainer_id", "score", "rating", "rating_label",
            "reasons", "warnings", "evaluation_basis",
        })

    def test_bad_rating_does_not_create_positive_claim(self):
        response = self.get_recommendation(pokemon_id=86)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual((data["score"], data["rating"]), (25, "bad"))
        self.assertEqual(data["reasons"], [])
        self.assertTrue(all("전기 타입 공격" in text and "4배" in text for text in data["warnings"]))
        self.assertEqual(len(data["warnings"]), 2)

    def test_zero_pokemon_id_is_valid(self):
        self.assertEqual(self.get_recommendation(pokemon_id=0).status_code, 200)

    def test_unknown_pokemon_returns_404_without_loading_trainer(self):
        response = self.get_recommendation(pokemon_id=999)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "존재하지 않는 포켓몬입니다.")
        self.get_trainer.assert_not_called()

    def test_unknown_trainer_returns_404(self):
        self.get_trainer.return_value = None
        response = self.get_recommendation(trainer_id="missing")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "존재하지 않는 인물입니다.")

    def test_invalid_or_missing_parameters_return_422_before_data_loading(self):
        cases = [
            {}, {"pokemon_id": 35}, {"trainer_id": "elesa"},
            {"pokemon_id": "abc", "trainer_id": "elesa"},
            {"pokemon_id": -1, "trainer_id": "elesa"},
            {"pokemon_id": 35, "trainer_id": ""},
            {"pokemon_id": 35, "trainer_id": " "},
            {"pokemon_id": 35, "trainer_id": " ele sa "},
        ]
        for params in cases:
            with self.subTest(params=params):
                self.assertEqual(self.client.get("/api/recommendations", params=params).status_code, 422)
        self.load_pokemon.assert_not_called()
        self.get_trainer.assert_not_called()

    def test_empty_party_returns_500(self):
        self.trainer["party"] = []
        self.assert_data_error()

    def test_broken_party_reference_returns_500(self):
        self.trainer["party"][0]["pokemon_id"] = 999
        self.assert_data_error()

    def test_invalid_pokemon_types_return_500(self):
        for types in ([], ["fairy"], ["water", "water"], "water", None):
            with self.subTest(types=types):
                self.pokemon[1]["types"] = types
                self.assert_data_error()

    def test_invalid_opponent_types_return_500(self):
        self.pokemon[3]["types"] = []
        self.assert_data_error()

    def test_data_read_failure_returns_500(self):
        self.load_pokemon.side_effect = OSError("private internal path")
        self.assert_data_error()

    def test_party_enrichment_does_not_mutate_trainer_data(self):
        self.assertEqual(self.get_recommendation().status_code, 200)
        self.assertNotIn("types", self.trainer["party"][0])
        self.assertNotIn("name", self.trainer["party"][0])

    def test_already_enriched_party_is_compatible(self):
        self.trainer["party"][0].update(name="에몽가", types=["electric", "flying"], image=None)
        self.assertEqual(self.get_recommendation().status_code, 200)

    def test_openapi_describes_inputs_and_all_output_fields(self):
        schema = self.client.get("/openapi.json").json()
        operation = schema["paths"]["/api/recommendations"]["get"]
        self.assertEqual({p["name"] for p in operation["parameters"]}, {"pokemon_id", "trainer_id"})
        self.assertTrue(all(p["required"] and p.get("description") for p in operation["parameters"]))
        fields = schema["components"]["schemas"]["Recommendation"]["properties"]
        self.assertTrue(all(p.get("description") for p in fields.values()))

    def assert_data_error(self):
        response = self.get_recommendation()
        self.assertEqual(response.status_code, 500, response.text)
        self.assertEqual(response.json()["detail"], "추천 계산에 필요한 데이터가 올바르지 않습니다.")
