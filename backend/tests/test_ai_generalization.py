"""실제 데이터의 모든 조합을 검사합니다. Ollama와 네트워크는 사용하지 않습니다."""

from collections import Counter
import json
from math import prod
import unittest
from unittest.mock import patch

from ai.explanation_service import build_explanation_catalog, generate_safe_explanation
from ai.recommendation_evidence import build_recommendation_evidence
from algorithm.type_chart import TYPE_CHART
from api.services import pokemon_service, recommendation_service, trainer_service


class AiGeneralizationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pokemon = pokemon_service.search_pokemon()
        cls.trainers = trainer_service.get_trainers()
        cls.by_id = {row["id"]: row for row in cls.pokemon}
        cls.cases = []
        for pokemon in cls.pokemon:
            for trainer in cls.trainers:
                evidence = build_recommendation_evidence(pokemon["id"], trainer["id"])
                existing = recommendation_service.get_recommendation(pokemon["id"], trainer["id"])
                catalog = build_explanation_catalog(evidence)
                cls.cases.append((pokemon, trainer, evidence, existing, catalog))

    def test_every_dataset_combination_keeps_score_direction_and_type_factors(self):
        self.assertTrue(self.pokemon)
        self.assertTrue(self.trainers)
        self.assertEqual(len(self.cases), len(self.pokemon) * len(self.trainers))
        seen_types = set()
        seen_multipliers = set()
        seen_ids = set()
        for pokemon, trainer, evidence, existing, catalog in self.cases:
            with self.subTest(pokemon_id=pokemon["id"], trainer_id=trainer["id"]):
                seen_ids.add(pokemon["id"])
                seen_types.update(pokemon["types"])
                for key in ("score", "rating", "rating_label"):
                    self.assertEqual(evidence[key], existing[key])
                self.assertEqual(evidence["pokemon"]["name"], pokemon["name"])
                self.assertEqual(evidence["trainer"]["trainer_id"], trainer["id"])
                expected_counts = Counter(member["pokemon_id"] for member in trainer["party"])
                self.assertEqual({row["opponent"]["pokemon_id"]: row["count"] for row in evidence["matchups"]}, dict(expected_counts))
                fact_counts = Counter()
                for matchup in evidence["matchups"]:
                    opponent = self.by_id[matchup["opponent"]["pokemon_id"]]
                    for name, attacker, defender in (
                        ("offense", pokemon, opponent), ("defense", opponent, pokemon),
                    ):
                        direction = matchup[name]
                        self.assertEqual(direction["attacker_name"], attacker["name"])
                        self.assertEqual(direction["defender_name"], defender["name"])
                        self.assertIn(direction["attack_type"], attacker["types"])
                        self.assertEqual([row["defense_type"] for row in direction["factors"]], defender["types"])
                        expected_factors = [TYPE_CHART[direction["attack_type"]].get(value, 1) for value in defender["types"]]
                        self.assertEqual([row["multiplier"] for row in direction["factors"]], expected_factors)
                        self.assertEqual(direction["multiplier"], prod(expected_factors))
                        possible = {
                            attack: prod(TYPE_CHART[attack].get(value, 1) for value in defender["types"])
                            for attack in attacker["types"]
                        }
                        self.assertEqual(direction["multiplier"], max(possible.values()))
                        multiplier = direction["multiplier"]
                        seen_multipliers.add(multiplier)
                        if multiplier != 1:
                            advantage = (name == "offense" and multiplier > 1) or (name == "defense" and multiplier < 1)
                            fact_counts["recommendation" if advantage else "warning"] += 1
                        if multiplier == 0:
                            immune_types = [row["defense_type_name"] for row in direction["factors"] if row["multiplier"] == 0]
                            self.assertTrue(immune_types)
                            self.assertTrue(all(value in direction["reason"] for value in immune_types))
                self.assertEqual(Counter(row["category"] for row in catalog["facts"]), fact_counts)
                self.assertEqual(len({row["id"] for row in catalog["facts"]}), len(catalog["facts"]))
        self.assertEqual(seen_ids, set(self.by_id))
        self.assertTrue({0, 0.25, 0.5, 1, 2, 4} <= seen_multipliers)
        self.assertEqual(seen_types, {value for pokemon in self.pokemon for value in pokemon["types"]})

    def test_valid_reversed_orders_preserve_every_fact_in_correct_section(self):
        for pokemon, trainer, evidence, _, catalog in self.cases:
            with self.subTest(pokemon_id=pokemon["id"], trainer_id=trainer["id"]):
                selection = {
                    "recommendation_order": [row["id"] for row in reversed(catalog["facts"]) if row["category"] == "recommendation"],
                    "warning_order": [row["id"] for row in reversed(catalog["facts"]) if row["category"] == "warning"],
                }
                with patch("ai.explanation_service.request_explanation", return_value={"raw_answer": json.dumps(selection)}) as request:
                    result = generate_safe_explanation(evidence)
                self.assertFalse(result["used_fallback"])
                self.assertEqual(result["ai_used"], bool(catalog["facts"]))
                self.assertEqual(request.call_count, int(bool(catalog["facts"])))
                self.assertEqual(result["score"], evidence["score"])
                self.assertEqual(result["selected_order"], selection)
                self.assertEqual(result["used_neutral_explanation"], not bool(catalog["facts"]))
                if not catalog["facts"]:
                    self.assertTrue(result["neutral_explanation"])
                    self.assertTrue(all(row["opponent"]["name"] in result["neutral_explanation"] for row in evidence["matchups"]))
                else:
                    self.assertIsNone(result["neutral_explanation"])
                by_id = {row["id"]: row["text"] for row in catalog["facts"]}
                for order, field in (("recommendation_order", "recommendation_reason"), ("warning_order", "warning")):
                    if selection[order]:
                        self.assertEqual(result[field], " ".join(by_id[value] for value in selection[order]))

    def test_timeout_fallback_preserves_every_fact_and_original_evidence(self):
        for pokemon, trainer, evidence, _, catalog in self.cases:
            with self.subTest(pokemon_id=pokemon["id"], trainer_id=trainer["id"]):
                before = json.dumps(evidence, ensure_ascii=False)
                with patch("ai.explanation_service.request_explanation", side_effect=TimeoutError("test timeout")):
                    result = generate_safe_explanation(evidence)
                self.assertFalse(result["ai_used"])
                self.assertEqual(result["used_fallback"], bool(catalog["facts"]))
                self.assertEqual(result["fallback_reason"], "timeout" if catalog["facts"] else None)
                self.assertEqual(result["score"], evidence["score"])
                self.assertEqual(result["evaluation_scope"], evidence["evaluation_basis"])
                self.assertEqual(json.dumps(evidence, ensure_ascii=False), before)
                for row in catalog["facts"]:
                    field = "recommendation_reason" if row["category"] == "recommendation" else "warning"
                    self.assertIn(row["text"], result[field])

    def test_missing_or_wrong_category_fact_always_uses_default_order(self):
        for pokemon, trainer, evidence, _, catalog in self.cases:
            if not catalog["facts"]:
                continue
            with self.subTest(pokemon_id=pokemon["id"], trainer_id=trainer["id"]):
                # The first required fact is placed in the other category.
                selection = {
                    "recommendation_order": [row["id"] for row in catalog["facts"] if row["category"] == "recommendation"],
                    "warning_order": [row["id"] for row in catalog["facts"] if row["category"] == "warning"],
                }
                first = catalog["facts"][0]
                original = "recommendation_order" if first["category"] == "recommendation" else "warning_order"
                other = "warning_order" if original == "recommendation_order" else "recommendation_order"
                selection[original].remove(first["id"])
                selection[other].append(first["id"])
                with patch("ai.explanation_service.request_explanation", return_value={"raw_answer": json.dumps(selection)}):
                    result = generate_safe_explanation(evidence)
                self.assertTrue(result["used_fallback"])
                self.assertEqual(result["fallback_reason"], "invalid_response")
                for row in catalog["facts"]:
                    field = "recommendation_reason" if row["category"] == "recommendation" else "warning"
                    self.assertIn(row["text"], result[field])


class RepresentativeCaseSelectionTest(unittest.TestCase):
    def test_selected_cases_cover_available_types_without_duplicates(self):
        from ai.generalization_demo import select_representative_cases
        report = select_representative_cases()
        self.assertEqual(report["dataset"]["combination_count"], report["dataset"]["pokemon_count"] * report["dataset"]["trainer_count"])
        self.assertFalse(report["uncovered_features"])
        covered = {feature for case in report["cases"] for feature in case["features"]}
        self.assertEqual(covered, set(report["available_features"]))
        keys = [(case["pokemon_id"], case["trainer_id"]) for case in report["cases"]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertGreater(len({case["pokemon_id"] for case in report["cases"]}), 1)

    def test_small_case_limit_reports_uncovered_types(self):
        from ai.generalization_demo import select_representative_cases
        report = select_representative_cases(max_cases=1)
        self.assertEqual(len(report["cases"]), 1)
        self.assertTrue(report["uncovered_features"])

    def test_invalid_case_count_is_rejected(self):
        from ai.generalization_demo import select_representative_cases
        for count in (0, -1, True):
            with self.assertRaises(ValueError):
                select_representative_cases(count)

    def test_default_script_execution_does_not_call_model(self):
        from ai.generalization_demo import main
        with patch("sys.argv", ["generalization_demo.py"]), patch("builtins.print"), \
                patch("ai.generalization_demo.generate_safe_explanation") as request:
            self.assertEqual(main(), 0)
            request.assert_not_called()


class NeutralExplanationTest(unittest.TestCase):
    def test_pidove_lenora_groups_opponents_and_keeps_both_directions(self):
        evidence = build_recommendation_evidence(25, "lenora")
        catalog = build_explanation_catalog(evidence)
        self.assertEqual(catalog["facts"], [])
        self.assertEqual(len(catalog["neutral_facts"]), 2)
        offense, defense = catalog["neutral_facts"]
        self.assertEqual(offense["direction"], "offense")
        self.assertEqual(defense["direction"], "defense")
        for fact in catalog["neutral_facts"]:
            self.assertEqual({row["name"] for row in fact["opponents"]}, {"하데리어", "보르그"})
            self.assertIn("1배입니다", fact["text"])
        self.assertIn("콩둘기의 노말 공격은 노말 타입인 하데리어·보르그에게", offense["text"])
        self.assertIn("하데리어·보르그의 노말 공격은 콩둘기에게", defense["text"])

    def test_all_neutral_result_has_detail_without_ai_or_fallback(self):
        evidence = build_recommendation_evidence(25, "lenora")
        with patch("ai.explanation_service.request_explanation") as request:
            result = generate_safe_explanation(evidence)
        request.assert_not_called()
        self.assertTrue(result["used_neutral_explanation"])
        self.assertFalse(result["ai_used"])
        self.assertFalse(result["used_fallback"])
        self.assertIsNone(result["fallback_reason"])
        self.assertEqual((result["score"], result["rating_label"]), (50, "보통"))
        self.assertIn("하데리어", result["neutral_explanation"])
        self.assertIn("보르그", result["neutral_explanation"])
        self.assertEqual(result["evaluation_scope"], evidence["evaluation_basis"])

    def test_mixed_matchups_keep_existing_ai_input_and_explanation_sections(self):
        evidence = build_recommendation_evidence(35, "elesa")
        catalog = build_explanation_catalog(evidence)
        self.assertTrue(catalog["neutral_facts"])
        raw = json.dumps({"recommendation_order": ["F1", "F2"], "warning_order": ["F3"]})
        with patch("ai.explanation_service.request_explanation", return_value={"raw_answer": raw}) as request:
            result = generate_safe_explanation(evidence)
        self.assertNotIn("neutral_facts", request.call_args.args[0])
        self.assertFalse(result["used_neutral_explanation"])
        self.assertIsNone(result["neutral_explanation"])
        self.assertTrue(result["ai_used"])
        self.assertEqual(result["score"], 54)
        self.assertIn("제브라이카", result["recommendation_reason"])
        self.assertIn("에몽가 2마리는 비행 타입이라 두더류의 땅 공격이 통하지 않습니다", result["warning"])

    def synthetic_evidence(self, pokemon, party):
        trainer = {"id": "test", "name": "실험 상대", "party": party}
        with patch("api.services.pokemon_service._load_pokemon", return_value=pokemon), \
                patch("api.services.trainer_service.get_trainer", return_value=trainer):
            return build_recommendation_evidence(0, "test")

    def test_two_times_and_half_cancel_to_neutral_with_explicit_factors(self):
        pokemon = [
            {"id": 0, "name": "내 포켓몬", "types": ["fire", "water"]},
            {"id": 1, "name": "상대", "types": ["grass", "water"]},
        ]
        evidence = self.synthetic_evidence(pokemon, [{"pokemon_id": 1}])
        with patch("ai.explanation_service.request_explanation") as request:
            result = generate_safe_explanation(evidence)
        request.assert_not_called()
        self.assertTrue(result["used_neutral_explanation"])
        self.assertIn("2 × 0.5 = 1", result["neutral_explanation"])
        self.assertIn("풀·물 타입", result["neutral_explanation"])
        self.assertEqual(result["score"], 50)

    def test_same_species_and_repeated_opponents_keep_count_and_direction(self):
        pokemon = [{"id": 0, "name": "같은 이름", "types": ["normal"]}]
        evidence = self.synthetic_evidence(pokemon, [{"pokemon_id": 0}, {"pokemon_id": 0}])
        facts = build_explanation_catalog(evidence)["neutral_facts"]
        self.assertEqual(len(facts), 2)
        self.assertIn("같은 이름의 노말 공격은 노말 타입인 같은 이름 2마리에게", facts[0]["text"])
        self.assertIn("같은 이름 2마리의 노말 공격은 같은 이름에게", facts[1]["text"])

    def test_demo_shows_neutral_detail_and_does_not_claim_model_request(self):
        from ai.ollama_demo import main
        evidence = build_recommendation_evidence(25, "lenora")
        with patch("sys.argv", ["ollama_demo.py", "--pokemon-id", "25", "--trainer-id", "lenora"]), \
                patch("ai.ollama_demo.build_recommendation_evidence", return_value=evidence), \
                patch("ai.explanation_service.request_explanation") as request, patch("builtins.print") as output:
            self.assertEqual(main(), 0)
        request.assert_not_called()
        output.assert_any_call("전체 등배 안내 사용:", "예")
        text = "\n".join(str(call.args) for call in output.call_args_list)
        self.assertIn("하데리어", text)
        self.assertIn("보르그", text)
        self.assertNotIn("선택 요청 중", text)


if __name__ == "__main__":
    unittest.main()
