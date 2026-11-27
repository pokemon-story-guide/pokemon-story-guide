import json
import unittest
from unittest.mock import patch
from urllib.error import URLError

from fastapi.testclient import TestClient

from api.main import app
from api.services.ai_explanation_service import RESPONSE_FIELDS

URL = "/api/recommendations/explanation"


class AiExplanationApiTest(unittest.TestCase):
    def setUp(self):
        settings = patch.dict("os.environ", {"OLLAMA_ENABLED": "true", "OLLAMA_TIMEOUT_SECONDS": "10"})
        settings.start()
        self.addCleanup(settings.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.pokemon = [
            {"id": 0, "name": "비크티니", "types": ["psychic", "fire"]},
            {"id": 35, "name": "두더류", "types": ["ground"]},
            {"id": 93, "name": "에몽가", "types": ["electric", "flying"]},
            {"id": 29, "name": "제브라이카", "types": ["electric"]},
            {"id": 25, "name": "콩둘기", "types": ["normal", "flying"]},
            {"id": 13, "name": "하데리어", "types": ["normal"]},
            {"id": 11, "name": "보르그", "types": ["normal"]},
        ]
        self.trainer = {"id": "elesa", "name": "카밀레", "party": [
            {"pokemon_id": 93, "level": 25}, {"pokemon_id": 93, "level": 25},
            {"pokemon_id": 29, "level": 27},
        ]}
        raw = json.dumps({"recommendation_order": ["F2", "F1"], "warning_order": ["F3"]})
        targets = [
            ("api.services.pokemon_service._load_pokemon", self.pokemon, "load_pokemon"),
            ("api.services.trainer_service.get_trainer", self.trainer, "get_trainer"),
            ("ai.explanation_service.request_explanation", {"raw_answer": raw}, "request_model"),
        ]
        for target, value, name in targets:
            mocker = patch(target, return_value=value)
            setattr(self, name, mocker.start())
            self.addCleanup(mocker.stop)

    def request(self, pokemon_id=35, trainer_id="elesa"):
        return self.client.post(URL, json={"pokemon_id": pokemon_id, "trainer_id": trainer_id})

    def test_valid_ai_order_returns_only_public_fields_and_ten_second_timeout(self):
        response = self.request()
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(set(data), {"pokemon_id", "trainer_id", *RESPONSE_FIELDS})
        self.assertEqual((data["pokemon_id"], data["trainer_id"]), (35, "elesa"))
        self.assertEqual((data["score"], data["rating"], data["rating_label"]), (54, "normal", "보통"))
        self.assertTrue(data["ai_used"])
        self.assertFalse(data["used_fallback"])
        self.assertFalse(data["used_neutral_explanation"])
        self.assertIsNone(data["neutral_explanation"])
        self.assertTrue(data["recommendation_reason"].startswith("두더류는 땅 타입이라"))
        self.assertIn("에몽가 2마리는 비행 타입이라", data["warning"])
        self.assertEqual(data["recommendation_reason"], " ".join(data["reasons"]))
        self.assertEqual(data["warning"], " ".join(data["warnings"]))
        self.assertEqual(len(data["reasons"]), 2)
        self.assertEqual(len(data["warnings"]), 1)
        self.assertEqual(self.request_model.call_args.kwargs["timeout"], 10)
        self.assertEqual(self.request_model.call_args.args[0]["score"], 54)
        self.assertIn("실제 기술·특성·능력치·레벨은 반영하지 않습니다", data["evaluation_scope"])

    def test_existing_single_evaluation_and_new_api_keep_same_scores(self):
        existing = self.client.get("/api/recommendations", params={"pokemon_id": 35, "trainer_id": "elesa"})
        response = self.request()
        self.assertEqual(existing.status_code, 200, existing.text)
        for key in ("score", "rating", "rating_label"):
            self.assertEqual(response.json()[key], existing.json()[key])

    def test_connection_failure_returns_200_with_fallback_and_no_internal_error(self):
        self.request_model.side_effect = URLError("PRIVATE_INTERNAL_ERROR")
        response = self.request()
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertFalse(data["ai_used"])
        self.assertTrue(data["used_fallback"])
        self.assertEqual(data["score"], 54)
        self.assertIn("에몽가", data["warning"])
        self.assertNotIn("PRIVATE_INTERNAL_ERROR", response.text)
        self.assertEqual(set(data), {"pokemon_id", "trainer_id", *RESPONSE_FIELDS})

    def test_timeout_returns_200_with_fallback(self):
        self.request_model.side_effect = TimeoutError("timed out")
        response = self.request()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["used_fallback"])
        self.assertFalse(response.json()["ai_used"])

    def test_invalid_or_incomplete_ai_choice_returns_fallback(self):
        for raw in (
            "not json",
            json.dumps({"recommendation_order": ["F1"], "warning_order": ["F3"]}),
            json.dumps({"recommendation_order": ["F1", "F9"], "warning_order": ["F3"]}),
        ):
            with self.subTest(raw=raw):
                self.request_model.return_value = {"raw_answer": raw}
                response = self.request()
                self.assertEqual(response.status_code, 200, response.text)
                self.assertTrue(response.json()["used_fallback"])
                self.assertEqual(response.json()["score"], 54)
                self.assertIn("제브라이카", response.json()["recommendation_reason"])
                self.assertIn("에몽가", response.json()["warning"])

    def test_all_neutral_returns_detail_without_calling_model(self):
        self.get_trainer.return_value = {"id": "lenora", "name": "알로에", "party": [
            {"pokemon_id": 13, "level": 18}, {"pokemon_id": 11, "level": 20},
        ]}
        response = self.request(25, "lenora")
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["score"], 50)
        self.assertTrue(data["used_neutral_explanation"])
        self.assertFalse(data["ai_used"])
        self.assertFalse(data["used_fallback"])
        self.assertIn("하데리어·보르그", data["neutral_explanation"])
        self.assertIn("서로 1배입니다", data["neutral_explanation"])
        self.assertEqual(data["reasons"], [])
        self.assertEqual(data["warnings"], [])
        self.request_model.assert_not_called()

    def test_zero_pokemon_id_is_accepted(self):
        self.request_model.side_effect = TimeoutError("test timeout")
        response = self.request(0)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["pokemon_id"], 0)

    def test_unknown_pokemon_returns_404_before_trainer_and_model_lookup(self):
        response = self.request(999)
        self.assertEqual(response.status_code, 404, response.text)
        self.assertEqual(response.json()["detail"], "존재하지 않는 포켓몬입니다.")
        self.get_trainer.assert_not_called()
        self.request_model.assert_not_called()

    def test_unknown_trainer_returns_404_without_model_call(self):
        self.get_trainer.return_value = None
        response = self.request(trainer_id="missing")
        self.assertEqual(response.status_code, 404, response.text)
        self.assertEqual(response.json()["detail"], "존재하지 않는 인물입니다.")
        self.request_model.assert_not_called()

    def test_invalid_request_returns_422_before_loading_data(self):
        cases = [
            {}, {"pokemon_id": 35}, {"trainer_id": "elesa"},
            {"pokemon_id": -1, "trainer_id": "elesa"},
            {"pokemon_id": "35", "trainer_id": "elesa"},
            {"pokemon_id": 35.5, "trainer_id": "elesa"},
            {"pokemon_id": True, "trainer_id": "elesa"},
            {"pokemon_id": None, "trainer_id": "elesa"},
            {"pokemon_id": 35, "trainer_id": ""},
            {"pokemon_id": 35, "trainer_id": " "},
            {"pokemon_id": 35, "trainer_id": "ele sa"},
            {"pokemon_id": 35, "trainer_id": "elesa\n"},
            {"pokemon_id": 35, "trainer_id": "elesa\u00a0"},
            {"pokemon_id": 35, "trainer_id": 1},
            {"pokemon_id": 35, "trainer_id": "elesa", "score": 100},
            {"pokemon_id": 35, "trainer_id": "elesa", "model": "another"},
            {"pokemon_id": 35, "trainer_id": "elesa", "timeout": 120},
            {"pokemon_id": 35, "trainer_id": "elesa", "OLLAMA_ENABLED": False},
            {"pokemon_id": 35, "trainer_id": "elesa", "OLLAMA_TIMEOUT_SECONDS": 120},
        ]
        for body in cases:
            with self.subTest(body=body):
                response = self.client.post(URL, json=body)
                self.assertEqual(response.status_code, 422, response.text)
        self.load_pokemon.assert_not_called()
        self.get_trainer.assert_not_called()
        self.request_model.assert_not_called()

    def test_missing_body_returns_422(self):
        self.assertEqual(self.client.post(URL).status_code, 422)
        self.load_pokemon.assert_not_called()
        self.request_model.assert_not_called()

    def test_invalid_source_data_returns_500_without_model_call(self):
        self.pokemon[1]["types"] = ["fairy"]
        response = self.request()
        self.assertEqual(response.status_code, 500, response.text)
        self.assertEqual(response.json()["detail"], "추천 설명에 필요한 데이터 또는 서버 설정이 올바르지 않습니다.")
        self.request_model.assert_not_called()

    def test_broken_party_reference_returns_500(self):
        self.trainer["party"][0]["pokemon_id"] = 999
        response = self.request()
        self.assertEqual(response.status_code, 500, response.text)
        self.request_model.assert_not_called()

    def test_empty_party_returns_500(self):
        self.trainer["party"] = []
        self.assertEqual(self.request().status_code, 500)
        self.request_model.assert_not_called()

    def test_source_read_failure_returns_500_not_fallback(self):
        self.load_pokemon.side_effect = OSError("PRIVATE_FILE_ERROR")
        response = self.request()
        self.assertEqual(response.status_code, 500, response.text)
        self.assertNotIn("PRIVATE_FILE_ERROR", response.text)
        self.request_model.assert_not_called()

    def test_disabled_model_returns_default_explanation_without_connection_attempt(self):
        with patch.dict("os.environ", {"OLLAMA_ENABLED": "false"}):
            response = self.request()
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertFalse(data["ai_used"])
        self.assertTrue(data["used_fallback"])
        self.assertFalse(data["used_neutral_explanation"])
        self.assertEqual(data["score"], 54)
        self.assertEqual(len(data["reasons"]), 2)
        self.assertEqual(len(data["warnings"]), 1)
        self.assertIn("에몽가", data["warnings"][0])
        self.request_model.assert_not_called()

    def test_timeout_is_configurable_on_server_only(self):
        with patch.dict("os.environ", {"OLLAMA_TIMEOUT_SECONDS": "30.5"}):
            response = self.request()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.request_model.call_args.kwargs["timeout"], 30.5)

    def test_invalid_server_timeout_returns_500_without_model_call(self):
        for value in ("0", "-1", "nan", "inf", "abc", ""):
            with self.subTest(value=value), patch.dict("os.environ", {"OLLAMA_TIMEOUT_SECONDS": value}):
                response = self.request()
                self.assertEqual(response.status_code, 500, response.text)
                self.assertEqual(response.json()["detail"], "추천 설명에 필요한 데이터 또는 서버 설정이 올바르지 않습니다.")
        self.request_model.assert_not_called()

    def test_invalid_enabled_setting_returns_500(self):
        with patch.dict("os.environ", {"OLLAMA_ENABLED": "maybe"}):
            response = self.request()
        self.assertEqual(response.status_code, 500, response.text)
        self.request_model.assert_not_called()

    def test_disabled_model_keeps_neutral_handling_separate_from_fallback(self):
        self.get_trainer.return_value = {"id": "lenora", "name": "알로에", "party": [
            {"pokemon_id": 13, "level": 18}, {"pokemon_id": 11, "level": 20},
        ]}
        with patch.dict("os.environ", {"OLLAMA_ENABLED": "false"}):
            response = self.request(25, "lenora")
        data = response.json()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(data["used_neutral_explanation"])
        self.assertFalse(data["used_fallback"])
        self.assertFalse(data["ai_used"])
        self.assertEqual(data["reasons"], [])
        self.assertEqual(data["warnings"], [])
        self.assertIn("하데리어", data["neutral_explanation"])
        self.request_model.assert_not_called()

    def test_disabled_model_does_not_hide_invalid_source_data(self):
        self.pokemon[1]["types"] = []
        with patch.dict("os.environ", {"OLLAMA_ENABLED": "false"}):
            response = self.request()
        self.assertEqual(response.status_code, 500, response.text)
        self.request_model.assert_not_called()

    def test_timeout_fallback_also_returns_lists_in_default_order(self):
        self.request_model.side_effect = TimeoutError("test timeout")
        data = self.request().json()
        self.assertTrue(data["used_fallback"])
        self.assertTrue(data["reasons"][0].startswith("제브라이카"))
        self.assertTrue(data["reasons"][1].startswith("두더류"))
        self.assertEqual(data["recommendation_reason"], " ".join(data["reasons"]))
        self.assertEqual(data["warning"], " ".join(data["warnings"]))

    def test_openapi_describes_request_response_and_errors(self):
        schema = self.client.get("/openapi.json").json()
        operation = schema["paths"][URL]["post"]
        self.assertIn("AI는 근거 순서만 선택", operation["description"])
        self.assertTrue(operation["requestBody"]["required"])
        self.assertTrue({"200", "404", "422", "500"} <= set(operation["responses"]))
        for name in ("AiExplanationRequest", "AiExplanationResponse"):
            fields = schema["components"]["schemas"][name]["properties"]
            self.assertTrue(all(field.get("description") for field in fields.values()))
        request_schema = schema["components"]["schemas"]["AiExplanationRequest"]
        self.assertFalse(request_schema["additionalProperties"])


class RealAiExplanationApiTest(unittest.TestCase):
    def test_representative_real_pairs_work_without_model_service(self):
        from api.services.recommendation_service import get_recommendation
        cases = [(25, "lenora"), (35, "elesa"), (113, "alder"), (23, "grimsley"), (36, "n-castle-black")]
        with TestClient(app) as client, patch("ai.explanation_service.request_explanation", side_effect=TimeoutError("test timeout")):
            for pokemon_id, trainer_id in cases:
                with self.subTest(pokemon_id=pokemon_id, trainer_id=trainer_id):
                    response = client.post(URL, json={"pokemon_id": pokemon_id, "trainer_id": trainer_id})
                    self.assertEqual(response.status_code, 200, response.text)
                    data = response.json()
                    existing = get_recommendation(pokemon_id, trainer_id)
                    for key in ("score", "rating", "rating_label"):
                        self.assertEqual(data[key], existing[key])
                    self.assertEqual(set(data), {"pokemon_id", "trainer_id", *RESPONSE_FIELDS})
                    self.assertFalse(data["ai_used"])
                    self.assertEqual(data["used_fallback"], not data["used_neutral_explanation"])


    def test_decimal_multiplier_stays_in_one_list_item(self):
        with TestClient(app) as client, patch.dict("os.environ", {"OLLAMA_ENABLED": "false"}):
            response = client.post(URL, json={"pokemon_id": 113, "trainer_id": "alder"})
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertTrue(any("0.25배" in text for text in data["reasons"]))
        self.assertTrue(all(text.endswith("습니다.") for text in data["reasons"]))
        self.assertEqual(data["recommendation_reason"], " ".join(data["reasons"]))


if __name__ == "__main__":
    unittest.main()
