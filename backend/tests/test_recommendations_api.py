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


class RecommendationEvidenceTest(unittest.TestCase):
    """AI 입력 근거와 기존 추천 API가 같은 계산 결과를 사용하는지 검증합니다."""

    def setUp(self):
        self.pokemon = [
            {"id": 35, "name": "두더류", "types": ["ground"]},
            {"id": 93, "name": "에몽가", "types": ["electric", "flying"]},
            {"id": 29, "name": "제브라이카", "types": ["electric"]},
        ]
        self.trainer = {"id": "elesa", "name": "카밀레", "party": [
            {"pokemon_id": 93, "level": 25},
            {"pokemon_id": 93, "level": 25},
            {"pokemon_id": 29, "level": 27},
        ]}
        for target, value in (
            ("api.services.pokemon_service._load_pokemon", self.pokemon),
            ("api.services.trainer_service.get_trainer", self.trainer),
        ):
            mocker = patch(target, return_value=value)
            mocker.start()
            self.addCleanup(mocker.stop)

    def evidence(self):
        from ai.recommendation_evidence import build_recommendation_evidence
        return build_recommendation_evidence(35, "elesa")

    def one_matchup(self, my_types, opponent_types):
        self.pokemon[0]["types"] = my_types
        self.pokemon[1]["types"] = opponent_types
        self.trainer["party"] = [self.trainer["party"][0]]
        return self.evidence()["matchups"][0]

    def test_ground_vs_emolga_explains_flying_immunity_and_keeps_count(self):
        evidence = self.evidence()
        self.assertEqual((evidence["score"], evidence["rating"]), (54, "normal"))
        self.assertEqual(len(evidence["matchups"]), 2)
        emolga = evidence["matchups"][0]
        self.assertEqual(emolga["count"], 2)
        self.assertEqual(emolga["opponent"]["type_names"], ["전기", "비행"])
        offense = emolga["offense"]
        self.assertEqual((offense["attacker_name"], offense["defender_name"]), ("두더류", "에몽가"))
        self.assertEqual([factor["multiplier"] for factor in offense["factors"]], [2, 0])
        self.assertEqual(offense["calculation"], "2 × 0 = 0")
        self.assertEqual(offense["effect"], "immune")
        self.assertIn("비행 타입이 땅 타입 공격을 무효화", offense["reason"])

    def test_defense_has_opposite_direction_and_correct_immunity_cause(self):
        zebra = self.evidence()["matchups"][1]
        defense = zebra["defense"]
        self.assertEqual((defense["attacker_name"], defense["defender_name"]), ("제브라이카", "두더류"))
        self.assertEqual(defense["attack_type"], "electric")
        self.assertEqual(defense["multiplier"], 0)
        self.assertIn("두더류의 땅 타입이 전기 타입 공격을 무효화", defense["reason"])
        self.assertEqual(zebra["offense"]["multiplier"], 2)

    def test_four_times_weakness_explains_both_factors(self):
        offense = self.one_matchup(["fire"], ["bug", "steel"])["offense"]
        self.assertEqual(offense["calculation"], "2 × 2 = 4")
        self.assertEqual(offense["effect"], "super_effective")
        self.assertIn("벌레 타입에 2배", offense["reason"])
        self.assertIn("강철 타입에 2배", offense["reason"])
        self.assertIn("최종 4배", offense["reason"])

    def test_quarter_resistance_explains_both_factors(self):
        offense = self.one_matchup(["fire"], ["water", "dragon"])["offense"]
        self.assertEqual(offense["calculation"], "0.5 × 0.5 = 0.25")
        self.assertEqual(offense["effect"], "resisted")
        self.assertIn("최종 0.25배", offense["reason"])

    def test_weakness_and_resistance_cancel_to_neutral(self):
        offense = self.one_matchup(["fire"], ["grass", "water"])["offense"]
        self.assertEqual(offense["calculation"], "2 × 0.5 = 1")
        self.assertEqual(offense["effect"], "neutral")
        self.assertIn("1배(등배)", offense["reason"])

    def test_single_type_neutral(self):
        offense = self.one_matchup(["normal"], ["water"])["offense"]
        self.assertEqual(offense["calculation"], "1 = 1")
        self.assertEqual(offense["effect"], "neutral")

    def test_defense_four_times_weakness(self):
        defense = self.one_matchup(["bug", "steel"], ["fire"])["defense"]
        self.assertEqual(defense["calculation"], "2 × 2 = 4")
        self.assertEqual(defense["defender_name"], "두더류")

    def test_selected_attack_and_threat_types_follow_algorithm(self):
        matchup = self.one_matchup(["ground", "water"], ["electric", "flying"])
        self.assertEqual(matchup["offense"]["attack_type"], "water")
        self.assertEqual(matchup["offense"]["multiplier"], 1)
        self.assertEqual(matchup["defense"]["attack_type"], "flying")
        self.assertEqual(matchup["defense"]["multiplier"], 1)

    def test_score_and_rating_match_existing_recommendation_api(self):
        evidence = self.evidence()
        with TestClient(app) as client:
            response = client.get("/api/recommendations", params={"pokemon_id": 35, "trainer_id": "elesa"})
            self.assertEqual(response.status_code, 200, response.text)
            for key in ("score", "rating", "rating_label"):
                self.assertEqual(evidence[key], response.json()[key])
        self.assertIn("실제 기술·특성·능력치·레벨은 반영하지 않습니다", evidence["evaluation_basis"])

    def test_unknown_pokemon_and_trainer_keep_404(self):
        from fastapi import HTTPException
        from ai.recommendation_evidence import build_recommendation_evidence
        with self.assertRaises(HTTPException) as error:
            build_recommendation_evidence(999, "elesa")
        self.assertEqual(error.exception.status_code, 404)
        with patch("api.services.trainer_service.get_trainer", return_value=None):
            with self.assertRaises(HTTPException) as error:
                self.evidence()
            self.assertEqual(error.exception.status_code, 404)

    def test_invalid_types_and_broken_party_references_are_rejected(self):
        self.pokemon[0]["types"] = ["fairy"]
        with self.assertRaises(ValueError):
            self.evidence()
        self.pokemon[0]["types"] = ["ground"]
        self.trainer["party"][0]["pokemon_id"] = 999
        with self.assertRaises(KeyError):
            self.evidence()

    def test_inconsistent_calculation_is_rejected(self):
        from ai.recommendation_evidence import _build_direction
        with self.assertRaisesRegex(ValueError, "일치하지"):
            _build_direction("두더류", "에몽가", "ground", ["electric", "flying"], 2)

    def test_preview_import_does_not_call_model_or_parse_arguments(self):
        import importlib
        import ai.ollama_demo
        with patch("urllib.request.urlopen") as request:
            importlib.reload(ai.ollama_demo)
            request.assert_not_called()


class RealRecommendationEvidenceTest(unittest.TestCase):
    def test_real_parties_keep_scores_and_all_multiplier_factors(self):
        from math import prod
        from ai.recommendation_evidence import build_recommendation_evidence
        from api.services import recommendation_service, trainer_service
        for trainer in trainer_service.get_trainers():
            with self.subTest(trainer_id=trainer["id"]):
                evidence = build_recommendation_evidence(35, trainer["id"])
                existing = recommendation_service.get_recommendation(35, trainer["id"])
                for key in ("score", "rating", "rating_label"):
                    self.assertEqual(evidence[key], existing[key])
                self.assertEqual(sum(row["count"] for row in evidence["matchups"]), len(trainer["party"]))
                for matchup in evidence["matchups"]:
                    for direction in ("offense", "defense"):
                        detail = matchup[direction]
                        self.assertEqual(prod(factor["multiplier"] for factor in detail["factors"]), detail["multiplier"])


class OllamaExplanationClientTest(unittest.TestCase):
    """CI에서 모델 호출은 대체하고 요청·응답 처리를 검증합니다."""

    def answer(self):
        return {"recommendation_order": ["F1", "F2"], "warning_order": ["F3"]}

    def response(self, **overrides):
        import io
        import json
        data = {"done": True, "done_reason": "stop", "message": {
            "content": json.dumps(self.answer()),
        }}
        data.update(overrides)
        return io.BytesIO(json.dumps(data).encode())

    def test_request_keeps_evidence_separate_from_system_instructions(self):
        import json
        from ai.ollama_client import request_explanation, validate_explanation_format
        evidence = {"score": 54, "rating_label": "보통", "facts": [{"id": "F1"}]}
        original = json.dumps(evidence)
        with patch("ai.ollama_client.urlopen", return_value=self.response()) as call:
            result = request_explanation(evidence, timeout=30)
        request = call.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/chat")
        self.assertEqual(request.method, "POST")
        self.assertEqual(payload["model"], "qwen2.5:7b")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["options"]["temperature"], 0)
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(json.loads(payload["messages"][1]["content"]), evidence)
        self.assertEqual(call.call_args.kwargs["timeout"], 30)
        self.assertEqual(json.dumps(evidence), original)
        self.assertEqual(validate_explanation_format(result["raw_answer"]), self.answer())

    def test_unfinished_and_truncated_model_responses_are_rejected(self):
        from ai.ollama_client import request_explanation
        for overrides in ({"done": False}, {"done_reason": "length"}):
            with patch("ai.ollama_client.urlopen", return_value=self.response(**overrides)):
                with self.assertRaises(ValueError):
                    request_explanation({})

    def test_malformed_model_envelope_is_rejected(self):
        from ai.ollama_client import request_explanation
        for overrides in ({"error": "model not found"}, {"message": None}, {"message": {"content": 123}}):
            with patch("ai.ollama_client.urlopen", return_value=self.response(**overrides)):
                with self.assertRaises(ValueError):
                    request_explanation({})

    def test_connection_failure_and_timeout_are_propagated(self):
        from urllib.error import URLError
        from ai.ollama_client import request_explanation
        for error in (URLError("connection refused"), TimeoutError("timed out")):
            with patch("ai.ollama_client.urlopen", side_effect=error):
                with self.assertRaises(type(error)):
                    request_explanation({})

    def test_invalid_model_or_timeout_does_not_send_request(self):
        from ai.ollama_client import request_explanation
        for options in ({"model": " "}, {"timeout": 0}, {"timeout": -1}, {"timeout": float("nan")}):
            with patch("ai.ollama_client.urlopen") as request:
                with self.assertRaises(ValueError):
                    request_explanation({}, **options)
                request.assert_not_called()

    def test_malformed_selection_fields_are_rejected(self):
        import json
        from ai.ollama_client import validate_explanation_format
        answers = [
            {}, [], {**self.answer(), "extra": "추가"},
            {**self.answer(), "warning_order": "F3"},
            {**self.answer(), "warning_order": [""]},
            {**self.answer(), "warning_order": [3]},
            {**self.answer(), "warning_order": ["F3", "F3"]},
        ]
        for answer in answers:
            with self.assertRaises(ValueError):
                validate_explanation_format(json.dumps(answer))

    def test_invalid_json_and_duplicate_fields_are_rejected(self):
        from ai.ollama_client import validate_explanation_format
        for raw in ('not json', '{"warning_order":[],"warning_order":[]}'):
            with self.assertRaises(ValueError):
                validate_explanation_format(raw)

    def test_preview_does_not_call_model(self):
        from ai.ollama_demo import main
        with patch("sys.argv", ["ollama_demo.py", "--preview-only"]), \
                patch("ai.ollama_demo.build_recommendation_evidence", return_value={}), \
                patch("ai.ollama_demo.build_explanation_catalog", return_value={}), \
                patch("ai.ollama_demo.generate_safe_explanation") as request, \
                patch("builtins.print"):
            self.assertEqual(main(), 0)
            request.assert_not_called()

    def test_demo_shows_fallback_and_completes(self):
        from ai.ollama_demo import main
        result = {
            "ai_raw_answer": None, "ai_used": False, "used_fallback": True,
            "fallback_reason": "connection_error", "ai_error": "connection refused",
            "elapsed_seconds": 0.1, "score": 54, "rating_label": "보통",
            "recommendation_reason": "기본 추천 설명", "warning": "기본 주의점",
            "evaluation_scope": "타입 상성 기준",
        }
        with patch("sys.argv", ["ollama_demo.py"]), \
                patch("ai.ollama_demo.build_recommendation_evidence", return_value={}), \
                patch("ai.ollama_demo.build_explanation_catalog", return_value={}), \
                patch("ai.ollama_demo.generate_safe_explanation", return_value=result), \
                patch("builtins.print") as output:
            self.assertEqual(main(), 0)
            output.assert_any_call("기본 설명으로 대체:", "예")


class SafeExplanationServiceTest(unittest.TestCase):
    def setUp(self):
        from ai.recommendation_evidence import build_recommendation_evidence
        self.evidence = build_recommendation_evidence(35, "elesa")

    def generate(self, answer):
        import json
        from ai.explanation_service import generate_safe_explanation
        raw = json.dumps(answer, ensure_ascii=False)
        with patch("ai.explanation_service.request_explanation", return_value={"raw_answer": raw}):
            return generate_safe_explanation(self.evidence)

    def test_catalog_categorizes_every_non_neutral_fact(self):
        from ai.explanation_service import build_explanation_catalog
        catalog = build_explanation_catalog(self.evidence)
        self.assertEqual([row["id"] for row in catalog["facts"]], ["F1", "F2", "F3"])
        self.assertEqual([row["category"] for row in catalog["facts"]], ["recommendation", "recommendation", "warning"])
        self.assertIn("2배", catalog["facts"][0]["text"])
        self.assertIn("두더류는 땅 타입이라 제브라이카의 전기 공격이 통하지 않습니다", catalog["facts"][1]["text"])
        self.assertIn("에몽가 2마리는 비행 타입이라 두더류의 땅 공격이 통하지 않습니다", catalog["facts"][2]["text"])

    def test_valid_order_only_changes_backend_sentence_order(self):
        result = self.generate({"recommendation_order": ["F2", "F1"], "warning_order": ["F3"]})
        self.assertTrue(result["ai_used"])
        self.assertFalse(result["used_fallback"])
        self.assertIsNone(result["fallback_reason"])
        self.assertTrue(result["recommendation_reason"].startswith("두더류는 땅 타입이라"))
        self.assertIn("제브라이카는 전기 타입이라 두더류의 땅 공격에 2배", result["recommendation_reason"])
        self.assertIn("에몽가 2마리는 비행 타입", result["warning"])
        self.assertEqual((result["score"], result["rating"], result["rating_label"]), (54, "normal", "보통"))
        self.assertEqual(result["evaluation_scope"], self.evidence["evaluation_basis"])

    def test_unknown_missing_wrong_category_and_duplicate_ids_fall_back(self):
        cases = [
            {"recommendation_order": ["F1", "F9"], "warning_order": ["F3"]},
            {"recommendation_order": ["F1"], "warning_order": ["F3"]},
            {"recommendation_order": ["F1", "F2"], "warning_order": []},
            {"recommendation_order": ["F1", "F3"], "warning_order": ["F2"]},
            {"recommendation_order": ["F1", "F1", "F2"], "warning_order": ["F3"]},
            {"recommendation_order": ["F1", "F2"], "warning_order": ["F3"], "score": 100},
            {"recommendation_reason": "비행 공격은 땅에 무효", "warning": "공격력이 감소"},
        ]
        for answer in cases:
            with self.subTest(answer=answer):
                result = self.generate(answer)
                self.assertFalse(result["ai_used"])
                self.assertTrue(result["used_fallback"])
                self.assertEqual(result["fallback_reason"], "invalid_response")
                self.assertEqual(result["selected_order"], {"recommendation_order": ["F1", "F2"], "warning_order": ["F3"]})
                self.assertIn("비행 타입이라 두더류의 땅 공격이 통하지", result["warning"])
                self.assertNotIn("공격력이 감소", result["warning"])
                self.assertEqual(result["score"], 54)

    def test_connection_failure_and_timeouts_return_default_explanations(self):
        from urllib.error import URLError
        from ai.explanation_service import generate_safe_explanation
        for error, reason in (
            (URLError("connection refused"), "connection_error"),
            (TimeoutError("timed out"), "timeout"),
            (URLError(TimeoutError("timed out")), "timeout"),
        ):
            with self.subTest(reason=reason):
                with patch("ai.explanation_service.request_explanation", side_effect=error):
                    result = generate_safe_explanation(self.evidence)
                self.assertFalse(result["ai_used"])
                self.assertTrue(result["used_fallback"])
                self.assertEqual(result["fallback_reason"], reason)
                self.assertTrue(result["recommendation_reason"])
                self.assertTrue(result["warning"])
                self.assertEqual(result["score"], 54)

    def test_invalid_json_uses_fallback_without_exposing_text_in_explanation(self):
        from ai.explanation_service import generate_safe_explanation
        with patch("ai.explanation_service.request_explanation", return_value={"raw_answer": "공격력이 증가합니다"}):
            result = generate_safe_explanation(self.evidence)
        self.assertTrue(result["used_fallback"])
        self.assertNotIn("공격력이 증가", result["recommendation_reason"])
        self.assertNotIn("공격력이 증가", result["warning"])

    def test_all_neutral_matchups_do_not_call_model(self):
        from ai.explanation_service import generate_safe_explanation
        from ai.recommendation_evidence import build_recommendation_evidence
        pokemon = [
            {"id": 0, "name": "내 포켓몬", "types": ["normal"]},
            {"id": 1, "name": "상대", "types": ["normal"]},
        ]
        trainer = {"id": "test", "name": "상대 트레이너", "party": [{"pokemon_id": 1}]}
        with patch("api.services.pokemon_service._load_pokemon", return_value=pokemon), \
                patch("api.services.trainer_service.get_trainer", return_value=trainer):
            evidence = build_recommendation_evidence(0, "test")
        with patch("ai.explanation_service.request_explanation") as request:
            result = generate_safe_explanation(evidence)
        request.assert_not_called()
        self.assertFalse(result["ai_used"])
        self.assertFalse(result["used_fallback"])
        self.assertIn("뚜렷한 이점이 없습니다", result["recommendation_reason"])
        self.assertIn("뚜렷한 주의점이 없습니다", result["warning"])
        self.assertEqual(result["score"], 50)

    def test_same_species_count_does_not_replace_our_own_pokemon(self):
        from ai.explanation_service import _fact_text
        from ai.recommendation_evidence import _build_direction
        direction = _build_direction("같은 이름", "같은 이름", "fire", ["fire"], 0.5)
        offense = _fact_text(direction, "offense", "같은 이름", 2)
        defense = _fact_text(direction, "defense", "같은 이름", 2)
        self.assertIn("같은 이름의 불꽃 공격에", offense)
        self.assertTrue(offense.startswith("같은 이름 2마리는 불꽃 타입이라"))
        self.assertIn("같은 이름 2마리의 불꽃 공격에", defense)
        self.assertTrue(defense.startswith("같은 이름은 불꽃 타입이라"))

    def test_original_evidence_is_unchanged(self):
        import json
        before = json.dumps(self.evidence, ensure_ascii=False)
        self.generate({"recommendation_order": ["F2", "F1"], "warning_order": ["F3"]})
        self.assertEqual(json.dumps(self.evidence, ensure_ascii=False), before)

    def test_corrupt_original_evidence_is_not_hidden_as_model_failure(self):
        from ai.explanation_service import generate_safe_explanation
        with patch("ai.explanation_service.request_explanation") as request:
            with self.assertRaises(KeyError):
                generate_safe_explanation({})
            request.assert_not_called()

    def test_fallback_preserves_all_facts_for_every_real_trainer(self):
        from ai.explanation_service import build_explanation_catalog, generate_safe_explanation
        from ai.recommendation_evidence import build_recommendation_evidence
        from api.services import trainer_service
        with patch("ai.explanation_service.request_explanation", side_effect=TimeoutError("test timeout")):
            for trainer in trainer_service.get_trainers():
                with self.subTest(trainer_id=trainer["id"]):
                    evidence = build_recommendation_evidence(35, trainer["id"])
                    catalog = build_explanation_catalog(evidence)
                    result = generate_safe_explanation(evidence)
                    for fact in catalog["facts"]:
                        field = "recommendation_reason" if fact["category"] == "recommendation" else "warning"
                        self.assertIn(fact["text"], result[field])
                    self.assertEqual(result["score"], evidence["score"])
