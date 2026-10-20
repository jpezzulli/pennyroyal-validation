import copy
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


common = load("validation_common", ROOT / "common.py")
reasoning_cases = load("reasoning_cases", ROOT / "cases/reasoning.py")
reasoning_runner = load("reasoning_runner", ROOT / "run-reasoning.py")
reasoning_scorer = load("reasoning_scorer", ROOT / "score-reasoning.py")
tool_runner = load("tool_runner", ROOT / "run-tools.py")
needle_runner = load("needle_runner", ROOT / "run-needle.py")
vision_runner = load("vision_runner", ROOT / "run-vision.py")


class ResponseExtractionTests(unittest.TestCase):
    def test_all_deepseek_response_fields(self):
        for field in ("reasoning", "reasoning_content"):
            reasoning, content = common.response_fragments(
                {"choices": [{"delta": {field: "hidden", "content": "visible"}}]}
            )
            self.assertEqual(reasoning, "hidden")
            self.assertEqual(content, "visible")

    def test_needle_fixture_smoke(self):
        self.assertTrue(needle_runner.fixture_smoke()["passed"])

    def test_needle_gate_requires_exact_visible_answer(self):
        manifest = {
            "actual_input_tokens": 994987,
            "target_input_tokens": 994987,
            "needle_start_zero_based_token": 154,
            "needle_present_in_any_response_field": True,
            "visible_content_exact_after_strip": False,
            "follow_up_passed": True,
            "error": None,
        }
        self.assertFalse(needle_runner.qualification_gate_passed(manifest))
        manifest["visible_content_exact_after_strip"] = True
        self.assertTrue(needle_runner.qualification_gate_passed(manifest))

    def test_vision_fixture_smoke(self):
        case = vision_runner.load_case()
        self.assertTrue(vision_runner.canonical_smoke(case)["passed"])

    def test_vision_gate_requires_both_spatial_endpoints(self):
        case = vision_runner.load_case()
        incomplete = (
            "Turbulent-Alps4046 reports 512k at 100+ tps with sglang + dflash2."
        )
        checks = vision_runner.evaluate_visible(
            incomplete, "stop", case["expected"]
        )
        self.assertFalse(checks["passed"])
        self.assertFalse(checks["bottom_author"])

    def test_vision_gate_rejects_mixed_claim_regions(self):
        case = vision_runner.load_case()
        mixed = (
            "Topmost: Turbulent-Alps4046 reports 200 tps on RTX Pro 6000 with "
            "SGLang. Bottommost: ComposerGen reports 512k and 100+ tps using "
            "sglang + dflash2."
        )
        checks = vision_runner.evaluate_visible(mixed, "stop", case["expected"])
        self.assertFalse(checks["passed"])
        self.assertFalse(checks["top_context"])
        self.assertFalse(checks["bottom_claim"])

    def test_vision_dry_run_is_non_inference(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "run-vision.py"), "--dry-run"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["mode"], "dry-run")


class ReasoningSuiteTests(unittest.TestCase):
    def setUp(self):
        self.grade = json.loads(
            (ROOT / "fixtures/reasoning-dspark4-grade.json").read_text()
        )
        self.rubric = json.loads(
            (ROOT / "cases/reasoning-rubric.json").read_text()
        )

    def score(self, grade=None):
        # The archived 2026-08-02 grade was locked before the genuine-loop-only
        # correction, so it is re-scored through the explicit legacy path.
        return reasoning_scorer.score_grade(
            grade or self.grade,
            reasoning_cases.CASES,
            self.rubric,
            legacy_loop_policy=True,
        )

    def test_frozen_request_count(self):
        self.assertEqual(len(reasoning_cases.CASES), 8)
        self.assertEqual(len(reasoning_runner.measured_plan(reasoning_cases)), 9)

    def test_reasoning_execution_profiles_preserve_case_order(self):
        sequential = reasoning_runner.execution_waves(
            reasoning_cases, reasoning_runner.SEQUENTIAL_PROFILE
        )
        self.assertEqual(
            [wave["case_ids"] for wave in sequential],
            [[f"C{index}"] for index in range(1, 9)],
        )
        three_user = reasoning_runner.execution_waves(
            reasoning_cases, reasoning_runner.THREE_USER_PROFILE
        )
        self.assertEqual(
            [wave["case_ids"] for wave in three_user],
            [["C1"], ["C2", "C3", "C4"], ["C5", "C6", "C7"], ["C8"]],
        )
        self.assertEqual(
            [case_id for wave in three_user for case_id in wave["case_ids"]],
            [f"C{index}" for index in range(1, 9)],
        )
        self.assertEqual(
            [wave["concurrency"] for wave in three_user], [1, 3, 3, 1]
        )

    def test_three_user_wave_starts_three_collectors_together(self):
        cases = reasoning_cases.CASES[1:4]
        lock = threading.Lock()
        active = 0
        peak_active = 0

        def collector(case, barrier):
            nonlocal active, peak_active
            barrier.wait()
            with lock:
                active += 1
                peak_active = max(peak_active, active)
            time.sleep(0.02)
            with lock:
                active -= 1
            return [case["id"]]

        result = reasoning_runner.execute_wave(cases, collector)
        self.assertEqual(list(result), ["C2", "C3", "C4"])
        self.assertEqual(peak_active, 3)

    def test_three_user_dry_run_reports_1_3_3_1_schedule(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "run-reasoning.py"),
                "--dry-run",
                "--execution-profile",
                reasoning_runner.THREE_USER_PROFILE,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(
            payload["execution_profile"], reasoning_runner.THREE_USER_PROFILE
        )
        self.assertEqual(
            [wave["case_ids"] for wave in payload["execution_waves"]],
            [["C1"], ["C2", "C3", "C4"], ["C5", "C6", "C7"], ["C8"]],
        )
        self.assertEqual(len(payload["measured_requests"]), 9)

    def test_sequential_list_keeps_historical_output_shape(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "run-reasoning.py"), "--list"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        lines = completed.stdout.splitlines()
        self.assertEqual(lines[0], "c1-r1\tC1\tturn 1")
        self.assertEqual(lines[-1], "c8-r1-correction\tC8\tturn 2")
        self.assertEqual(len(lines), 9)

    def test_measured_requests_have_no_output_token_cap(self):
        payload = reasoning_runner.measured_payload("pennyroyal", [])
        self.assertNotIn("max_tokens", payload)
        self.assertNotIn("max_completion_tokens", payload)

    def test_dependency_free_loop_units_are_stable(self):
        text = "Alpha, beta! Alpha, beta!"
        units = reasoning_runner.loop_detection_units(text)
        self.assertEqual(units, reasoning_runner.loop_detection_units(text))
        self.assertEqual(
            units,
            ["Alpha", ",", "beta", "!", "Alpha", ",", "beta", "!"],
        )

    def test_reasoning_cli_does_not_expose_model_tokenizer_path(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "run-reasoning.py"), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertNotIn("--tokenizer-path", completed.stdout)

    def test_chat_completion_usage_is_authoritative(self):
        self.assertEqual(
            reasoning_runner.completion_token_count({"completion_tokens": 123}),
            123,
        )
        self.assertIsNone(reasoning_runner.completion_token_count(None))

    def test_public_replay_fixture_passes(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "run-reasoning.py"),
                "--replay",
                str(ROOT / "fixtures/reasoning-replay.jsonl"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["gate_passed"])

    def test_historical_grade_reproduces_published_score(self):
        result = self.score()
        self.assertEqual(result["final_score"], 97.07)
        self.assertLess(result["case_scores"]["C5"], 100)

    def test_missing_c5_correctness_is_rejected(self):
        grade = copy.deepcopy(self.grade)
        del grade["cases"]["C5"]["correctness"]
        with self.assertRaisesRegex(ValueError, r"C5.*missing=.*correctness"):
            self.score(grade)

    def test_only_c5_correctness_is_rejected(self):
        grade = copy.deepcopy(self.grade)
        grade["cases"]["C5"] = {"correctness": 4}
        with self.assertRaisesRegex(ValueError, r"C5.*missing="):
            self.score(grade)

    def test_unauthorized_dimension_is_rejected(self):
        grade = copy.deepcopy(self.grade)
        grade["cases"]["C5"]["presentation_polish"] = 4
        with self.assertRaisesRegex(
            ValueError, r"C5.*unexpected=.*presentation_polish"
        ):
            self.score(grade)

    def test_revision_quality_is_rejected_outside_c8(self):
        grade = copy.deepcopy(self.grade)
        grade["cases"]["C1"]["revision_quality"] = 4
        with self.assertRaisesRegex(
            ValueError, r"C1.*unexpected=.*revision_quality"
        ):
            self.score(grade)

    def test_complete_c8_dimension_set_is_accepted(self):
        expected = reasoning_scorer.expected_case_dimensions("C8", self.rubric)
        supplied = set(self.grade["cases"]["C8"]) - {"note"}
        self.assertEqual(supplied, expected)
        self.assertEqual(self.score()["final_score"], 97.07)


class ReasoningLoopPenaltyPolicyTests(unittest.TestCase):
    """Repetition and long xhigh deliberation are not quality detractors."""

    def setUp(self):
        self.rubric = json.loads(
            (ROOT / "cases/reasoning-rubric.json").read_text(encoding="utf-8")
        )

    def full_credit_grade(self):
        grade = {
            "candidate_id": "candidate-loop-policy",
            "scale": "0-4",
            "fatal_findings": [],
            "cases": {},
        }
        for case in reasoning_cases.CASES:
            dimensions = reasoning_scorer.expected_case_dimensions(
                case["id"], self.rubric
            )
            entry = {dimension: 4 for dimension in sorted(dimensions)}
            entry["note"] = (
                "Long xhigh trace: rechecked assumptions, revisited two "
                "alternatives, redrew the derivation, then concluded."
            )
            grade["cases"][case["id"]] = entry
        return grade

    def score(self, grade, **kwargs):
        return reasoning_scorer.score_grade(
            grade, reasoning_cases.CASES, self.rubric, **kwargs
        )

    def test_full_credit_xhigh_reconsideration_keeps_full_marks(self):
        result = self.score(self.full_credit_grade())
        self.assertEqual(result["final_score"], 100.0)
        self.assertEqual(result["fatal_findings"], [])
        self.assertEqual(
            result["loop_policy"], self.rubric["loop_policy"]["version"]
        )

    def test_unsupported_loop_deduction_without_evidence_is_rejected(self):
        grade = self.full_credit_grade()
        grade["cases"]["C4"]["loop_behavior"] = 2
        with self.assertRaisesRegex(ValueError, "C4.*loop_behavior"):
            self.score(grade)

    def test_repetition_only_loop_deduction_is_rejected(self):
        grade = self.full_credit_grade()
        grade["cases"]["C4"]["loop_behavior"] = 2
        grade["cases"]["C4"]["deduction_justifications"] = {
            "loop_behavior": {
                "category": "verbosity",
                "evidence": "the reasoning was long and repetitive",
            }
        }
        with self.assertRaisesRegex(ValueError, "non-detractor"):
            self.score(grade)

    def test_answer_defect_cannot_dock_loop_behavior(self):
        grade = self.full_credit_grade()
        grade["cases"]["C4"]["loop_behavior"] = 0
        grade["cases"]["C4"]["deduction_justifications"] = {
            "loop_behavior": {
                "category": "incorrect_final_conclusion",
                "evidence": "A wrong conclusion but no loop.",
            }
        }
        with self.assertRaisesRegex(ValueError, "only be docked for a genuine-loop"):
            self.score(grade)

    def test_every_docked_dimension_needs_substantive_evidence(self):
        docked = (
            ("C8", "revision_quality"),
            ("C1", "correctness"),
            ("C2", "evidence_discipline"),
            ("C3", "constraint_preservation"),
            ("C4", "contradiction_detection"),
            ("C5", "unsupported_assumptions"),
            ("C6", "confidence_calibration"),
            ("C7", "final_answer_usability"),
        )
        for case_id, dimension in docked:
            with self.subTest(case_id=case_id, dimension=dimension):
                grade = self.full_credit_grade()
                grade["cases"][case_id][dimension] = 0
                grade["cases"][case_id]["note"] = (
                    "Repetitive reconsideration and long reasoning; the final "
                    "answer and the correction are correct."
                )
                with self.assertRaisesRegex(ValueError, dimension):
                    self.score(grade)

    def test_genuine_loop_category_cannot_dock_an_answer_dimension(self):
        grade = self.full_credit_grade()
        grade["cases"]["C5"]["loop_behavior"] = 2
        grade["cases"]["C5"]["technical_reasoning"] = 2
        grade["cases"]["C5"]["deduction_justifications"] = {
            "loop_behavior": {
                "category": "non_converging_repetition",
                "evidence": "successive restatements add no new work",
            },
            "technical_reasoning": {
                "category": "non_converging_repetition",
                "evidence": "the trace was long",
            },
        }
        with self.assertRaisesRegex(
            ValueError, "charged only through loop_behavior"
        ):
            self.score(grade)

    def test_substantive_deduction_in_an_answer_dimension_is_accepted(self):
        accepted = (
            ("C1", "correctness", "unsupported_claim"),
            ("C2", "evidence_discipline", "unsupported_claim"),
            ("C3", "constraint_preservation", "missed_explicit_requirement"),
            ("C4", "technical_reasoning", "incomplete_proof"),
            ("C4", "contradiction_detection", "incomplete_proof"),
            ("C5", "unsupported_assumptions", "unsupported_claim"),
            ("C6", "confidence_calibration", "unsupported_claim"),
            ("C7", "final_answer_usability", "missing_or_unusable_final_answer"),
            ("C8", "revision_quality", "failed_correction"),
        )
        for case_id, dimension, category in accepted:
            with self.subTest(case_id=case_id, dimension=dimension):
                grade = self.full_credit_grade()
                grade["cases"][case_id][dimension] = 2
                grade["cases"][case_id]["deduction_justifications"] = {
                    dimension: {
                        "category": category,
                        "evidence": "quoted from the blinded response text",
                    }
                }
                result = self.score(grade)
                self.assertLess(result["final_score"], 100)
                self.assertLess(result["case_scores"][case_id], 100)
                self.assertEqual(result["dimension_averages"]["loop_behavior"], 4.0)
                untouched = "C1" if case_id != "C1" else "C2"
                self.assertEqual(result["case_scores"][untouched], 100)

    def test_evidence_backed_genuine_loop_is_still_penalized(self):
        grade = self.full_credit_grade()
        grade["cases"]["C5"]["loop_behavior"] = 1
        grade["cases"]["C5"]["deduction_justifications"] = {
            "loop_behavior": {
                "category": "identical_block_repeat",
                "evidence": (
                    "one 392-token block recurs four consecutive times and the "
                    "response never emits a final answer"
                ),
            }
        }
        grade["fatal_findings"] = [
            {"cap": "confirmed_reasoning_loop", "case_id": "C5"}
        ]
        result = self.score(grade)
        self.assertEqual(result["final_score"], 20)
        self.assertLess(result["case_scores"]["C5"], 100)
        self.assertEqual(result["case_scores"]["C1"], 100)
        self.assertEqual(result["dimension_averages"]["correctness"], 4.0)
        self.assertEqual(result["dimension_averages"]["loop_behavior"], 3.52)

    def test_genuine_loop_claim_without_loop_deduction_is_rejected(self):
        grade = self.full_credit_grade()
        grade["cases"]["C3"]["deduction_justifications"] = {
            "loop_behavior": {
                "category": "non_converging_repetition",
                "evidence": "the same proof is restated without progress",
            }
        }
        with self.assertRaisesRegex(ValueError, "full credit"):
            self.score(grade)

    def test_similarity_flag_or_output_cap_alone_cannot_confirm_a_loop_cap(self):
        for cap in (
            "confirmed_reasoning_loop",
            "repetitive_32768_exhaustion_without_usable_answer",
        ):
            with self.subTest(cap=cap):
                grade = self.full_credit_grade()
                grade["fatal_findings"] = [{"cap": cap, "case_id": "C5"}]
                with self.assertRaisesRegex(ValueError, cap):
                    self.score(grade)

    def test_unusable_final_answer_supports_the_exhaustion_cap(self):
        grade = self.full_credit_grade()
        grade["cases"]["C5"]["loop_behavior"] = 1
        grade["cases"]["C5"]["final_answer_usability"] = 1
        grade["cases"]["C5"]["deduction_justifications"] = {
            "loop_behavior": {
                "category": "non_converging_repetition",
                "evidence": "successive restatements add no new work",
            },
            "final_answer_usability": {
                "category": "missing_or_unusable_final_answer",
                "evidence": "no visible final answer was produced",
            },
        }
        grade["fatal_findings"] = [
            {
                "cap": "repetitive_32768_exhaustion_without_usable_answer",
                "case_id": "C5",
            }
        ]
        self.assertEqual(self.score(grade)["final_score"], 10)

    def test_guarded_cap_cannot_rest_on_an_unrelated_case(self):
        for cap, supporting_dimension, category in (
            (
                "repetitive_32768_exhaustion_without_usable_answer",
                "final_answer_usability",
                "missing_or_unusable_final_answer",
            ),
            (
                "confirmed_reasoning_loop",
                "loop_behavior",
                "non_converging_repetition",
            ),
        ):
            with self.subTest(cap=cap):
                grade = self.full_credit_grade()
                grade["cases"]["C1"][supporting_dimension] = 2
                grade["cases"]["C1"]["deduction_justifications"] = {
                    supporting_dimension: {
                        "category": category,
                        "evidence": "an unrelated, real deduction on C1",
                    }
                }
                grade["fatal_findings"] = [{"cap": cap, "case_id": "C5"}]
                with self.assertRaisesRegex(ValueError, r"C5"):
                    self.score(grade)

    def test_undocked_annotation_cannot_confirm_a_guarded_cap(self):
        grade = self.full_credit_grade()
        grade["cases"]["C1"]["deduction_justifications"] = {
            "final_answer_usability": {
                "category": "missing_or_unusable_final_answer",
                "evidence": "An unrelated absence claim.",
            }
        }
        grade["fatal_findings"] = [
            {
                "cap": "repetitive_32768_exhaustion_without_usable_answer",
                "case_id": "C5",
            }
        ]
        with self.assertRaisesRegex(ValueError, "full credit"):
            self.score(grade)

    def test_guarded_cap_requires_a_case_id(self):
        grade = self.full_credit_grade()
        grade["cases"]["C5"]["loop_behavior"] = 1
        grade["cases"]["C5"]["deduction_justifications"] = {
            "loop_behavior": {
                "category": "identical_block_repeat",
                "evidence": "the same 64-token block recurs four times",
            }
        }
        grade["fatal_findings"] = [{"cap": "confirmed_reasoning_loop"}]
        with self.assertRaisesRegex(ValueError, "case_id"):
            self.score(grade)
        for unknown in ("C9", "", None):
            with self.subTest(case_id=unknown):
                grade = self.full_credit_grade()
                grade["cases"]["C5"]["loop_behavior"] = 1
                grade["cases"]["C5"]["deduction_justifications"] = {
                    "loop_behavior": {
                        "category": "identical_block_repeat",
                        "evidence": "the same 64-token block recurs four times",
                    }
                }
                grade["fatal_findings"] = [
                    {"cap": "confirmed_reasoning_loop", "case_id": unknown}
                ]
                with self.assertRaisesRegex(ValueError, "case_id"):
                    self.score(grade)

    def test_guarded_cap_rejects_wrong_supporting_dimension(self):
        grade = self.full_credit_grade()
        grade["cases"]["C5"]["final_answer_usability"] = 1
        grade["cases"]["C5"]["deduction_justifications"] = {
            "final_answer_usability": {
                "category": "missed_explicit_requirement",
                "evidence": "the answer omitted a required field",
            }
        }
        grade["fatal_findings"] = [
            {
                "cap": "repetitive_32768_exhaustion_without_usable_answer",
                "case_id": "C5",
            }
        ]
        with self.assertRaisesRegex(ValueError, "missing_or_unusable_final_answer"):
            self.score(grade)

    def test_same_case_evidence_supports_both_guarded_caps(self):
        grade = self.full_credit_grade()
        grade["cases"]["C5"]["loop_behavior"] = 1
        grade["cases"]["C5"]["final_answer_usability"] = 1
        grade["cases"]["C5"]["deduction_justifications"] = {
            "loop_behavior": {
                "category": "identical_block_repeat",
                "evidence": "one block recurs four consecutive times",
            },
            "final_answer_usability": {
                "category": "missing_or_unusable_final_answer",
                "evidence": "no visible final answer was produced",
            },
        }
        grade["fatal_findings"] = [
            {"cap": "confirmed_reasoning_loop", "case_id": "C5"},
            {
                "cap": "repetitive_32768_exhaustion_without_usable_answer",
                "case_id": "C5",
            },
        ]
        result = self.score(grade)
        self.assertEqual(result["final_score"], 10)
        self.assertEqual(result["case_scores"]["C1"], 100)

    def test_repetition_cannot_be_smuggled_into_other_dimensions(self):
        for dimension, category in (
            ("technical_reasoning", "reconsideration"),
            ("final_answer_usability", "output_length"),
        ):
            with self.subTest(dimension=dimension):
                grade = self.full_credit_grade()
                grade["cases"]["C3"][dimension] = 3
                grade["cases"]["C3"]["deduction_justifications"] = {
                    dimension: {
                        "category": category,
                        "evidence": "the answer spent too long deliberating",
                    }
                }
                with self.assertRaisesRegex(ValueError, "non-detractor"):
                    self.score(grade)

    def test_archived_grade_needs_the_explicit_legacy_flag(self):
        archived = json.loads(
            (ROOT / "fixtures/reasoning-dspark4-grade.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            self.score(archived, legacy_loop_policy=True)["final_score"], 97.07
        )
        with self.assertRaisesRegex(ValueError, "legacy-loop-policy"):
            self.score(archived)

    def test_exported_grading_packet_communicates_the_rule(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet_path = Path(temporary) / "grading-packet.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "anonymize-reasoning.py"),
                    "--suite",
                    str(ROOT / "cases/reasoning.py"),
                    "--results",
                    str(ROOT / "fixtures/reasoning-replay.jsonl"),
                    "--output",
                    str(packet_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            packets = json.loads(packet_path.read_text(encoding="utf-8"))
        self.assertEqual(len(packets), len(reasoning_cases.CASES))
        for packet in packets:
            guidance = packet["grading_guidance"]
            policy = guidance["loop_policy"]
            self.assertEqual(policy["version"], "genuine-loop-only-v1")
            self.assertIn("repetition", policy["non_detractors"])
            self.assertIn("unsupported_claim", policy["substantive_defect_categories"])
            self.assertIn(
                "non_converging_repetition", policy["genuine_loop_categories"]
            )
            self.assertNotIn(
                "repetition", policy["substantive_defect_categories"]
            )
            self.assertEqual(
                guidance["required_justification_field"],
                "deduction_justifications",
            )
            self.assertIn("not deductions", guidance["loop_penalties"])
            self.assertIn("Every dimension", guidance["loop_penalties"])
            self.assertIn("only for a genuine-loop", guidance["loop_penalties"])

    def test_protocol_copies_state_the_rule(self):
        for path in (
            ROOT / "cases/reasoning-protocol.md",
            ROOT.parent / "reasoning/design/protocol.md",
        ):
            self.assertIn("Repetition is not a defect", path.read_text(encoding="utf-8"), str(path))

    def test_canonical_rubric_copies_match(self):
        current = (ROOT / "cases/reasoning-rubric.json").read_text(encoding="utf-8")
        design = (ROOT.parent / "reasoning/design/rubric.json").read_text(encoding="utf-8")
        self.assertEqual(current, design)

    def test_case_document_no_longer_calls_long_answers_detracting(self):
        text = (ROOT.parent / "docs/cases/reasoning.md").read_text(encoding="utf-8")
        self.assertNotIn("may lose loop-efficiency", text)
        self.assertIn("genuine-loop-only", text)

    def test_hard_loop_detection_still_flags_real_loops(self):
        block = " ".join(f"token{index}" for index in range(64)) + " "
        units = reasoning_runner.loop_detection_units(block * 4)
        self.assertEqual(
            reasoning_runner.exact_block_loop(units),
            {"type": "exact_block_x4", "block_tokens": 64},
        )
        sentence = "The same derivation is repeated again and again here. " * 10
        self.assertEqual(
            reasoning_runner.sentence_loop(sentence)["type"],
            "normalized_sentence_x10",
        )


class ToolSuiteTests(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads(
            (ROOT / "fixtures/tools-dspark4-replay.json").read_text()
        )

    def assert_plan_rejected(self, rows):
        result = tool_runner.score_rows(rows)
        self.assertFalse(result["gate_passed"])
        self.assertFalse(result["schedule_integrity"]["passed"])
        self.assertTrue(result["schedule_integrity"]["mismatches"])
        return result

    def test_frozen_invocation_count_and_public_definition(self):
        self.assertEqual(len(tool_runner.invocation_plan()), 30)
        definition = json.loads((ROOT / "cases/tools.json").read_text())
        self.assertEqual(len(definition["ordinary_cases"]), 14)
        self.assertEqual(len(definition["concurrent_cases"]), 3)
        self.assertEqual(definition["system_message"], tool_runner.SYSTEM_MESSAGE)
        self.assertEqual(definition["tool_schemas"], tool_runner.TOOLS)
        self.assertEqual(definition["ordinary_cases"], tool_runner.CASES)
        self.assertEqual(definition["concurrent_cases"], tool_runner.CONCURRENT)

    def test_sealed_controls_are_opt_in_and_versioned(self):
        self.assertEqual(len(tool_runner.invocation_plan()), 30)
        self.assertEqual(
            set(tool_runner.SEALED_CONTROLS),
            {"agentic", "natural-decode"},
        )
        self.assertEqual(
            tool_runner.SEALED_CONTROLS["agentic"]["id"],
            "sealed_agentic_release_note_v2",
        )
        self.assertEqual(
            tool_runner.SEALED_CONTROLS["natural-decode"]["id"],
            "sealed_natural_decode_v2",
        )
        decode = tool_runner.SEALED_CONTROLS["natural-decode"]
        self.assertEqual(decode["max_tokens"], 3072)
        self.assertEqual(decode["reasoning_effort"], "low")
        self.assertEqual(decode["temperature"], 0.0)
        self.assertTrue(decode["return_token_ids"])
        self.assertTrue(
            set(tool_runner.SEALED_TOOLS).isdisjoint(tool_runner.TOOLS)
        )

    def test_generated_stream_digests_cover_direct_token_ids_and_output(self):
        turns = [
            {
                "response": {
                    "choices": [
                        {
                            "token_ids": [17, 23, 41],
                            "message": {
                                "reasoning_content": "brief",
                                "content": "answer",
                            },
                        }
                    ]
                }
            }
        ]
        first = tool_runner.generated_stream_digests(turns)
        second = tool_runner.generated_stream_digests(copy.deepcopy(turns))
        self.assertEqual(first, second)
        self.assertEqual(first["token_id_count"], 3)
        changed = copy.deepcopy(turns)
        changed[0]["response"]["choices"][0]["token_ids"][-1] = 42
        self.assertNotEqual(
            first["token_ids_sha256"],
            tool_runner.generated_stream_digests(changed)["token_ids_sha256"],
        )

    def test_journal_analysis_preserves_execution_path_metrics(self):
        lines = [
            (
                "Engine: Avg generation throughput: 81.5 tokens/s, "
                "Prefix cache hit rate: 0.0%"
            ),
            (
                "SpecDecoding metrics: Accepted: 120 tokens, "
                "Drafted: 200 tokens"
            ),
            "torch.compile graph capture occurred",
        ]
        result = tool_runner.journal_analysis(lines)
        self.assertEqual(result["engine_generation_throughput_samples"], [81.5])
        self.assertEqual(result["journal_accepted_tokens_total"], 120)
        self.assertEqual(result["journal_drafted_tokens_total"], 200)
        self.assertEqual(result["journal_acceptance_rate"], 0.6)
        self.assertEqual(result["prefix_cache_hit_rate_samples"], [0.0])
        self.assertEqual(
            result["compile_jit_cuda_graph_activity"],
            ["torch.compile graph capture occurred"],
        )

    def test_sealed_agentic_artifact_requires_real_revision(self):
        state = {}
        created = tool_runner.execute_tool(
            "create_release_note",
            {
                "title": "Atlas release readiness",
                "markdown": (
                    "# Summary\n12 of 20 nodes validated; 8 nodes remain.\n"
                    "# Schedule\n2026-09-02 22:00 UTC\n"
                    "# Owner\nRiley Chen; rollback: Morgan Lee\n"
                    "# Risk\n8 nodes remain unvalidated.\n"
                    "# Next Action\nValidate by 2026-09-01 18:00 UTC"
                ),
            },
            state,
        )
        first = tool_runner.execute_tool(
            "inspect_release_note",
            {"artifact_id": created["artifact_id"]},
            state,
        )
        self.assertEqual(first["status"], "needs_revision")
        revised = tool_runner.execute_tool(
            "revise_release_note",
            {
                "artifact_id": created["artifact_id"],
                "title": state["release_note"]["title"],
                "markdown": state["release_note"]["markdown"],
                "review_acknowledgement": "8 nodes remain unvalidated",
            },
            state,
        )
        final = tool_runner.execute_tool(
            "inspect_release_note",
            {"artifact_id": revised["artifact_id"]},
            state,
        )
        self.assertEqual(revised["version"], 2)
        self.assertEqual(final["status"], "passed")

    def test_agentic_gate_uses_artifact_state_not_redundant_version_prose(self):
        artifact = {
            "artifact_id": "NOTE-ATLAS-17",
            "version": 2,
            "title": "Atlas release readiness",
            "markdown": (
                "# Summary\n12 of 20 nodes validated; 8 nodes remain.\n"
                "# Schedule\n2026-09-02 22:00 UTC\n"
                "# Owner\nRiley Chen; rollback: Morgan Lee\n"
                "# Risk\n8 nodes remain unvalidated.\n"
                "# Next Action\nValidate by 2026-09-01 18:00 UTC"
            ),
            "review_acknowledgement": "8 nodes remain unvalidated",
        }
        names = [
            "inspect_release_brief",
            "create_release_note",
            "inspect_release_note",
            "revise_release_note",
            "inspect_release_note",
        ]
        calls = [{"name": name, "arguments": {}, "result": {}} for name in names]
        calls[2]["result"] = {"status": "needs_revision"}
        calls[4]["result"] = {
            "artifact_id": "NOTE-ATLAS-17",
            "version": 2,
            "status": "passed",
            "issues": [],
        }
        result = {
            "case_id": "sealed_agentic_release_note_v2",
            "calls": calls,
            "final_tool_state": {"release_note": artifact},
            "final": "Artifact NOTE-ATLAS-17 passed its final inspection.",
            "finish_reason": "stop",
            "model_turn_count": 6,
            "tool_call_count": 5,
            "error": None,
        }
        scored = tool_runner.evaluate_control(result)
        self.assertTrue(scored["score"]["passed"])
        self.assertFalse(
            scored["score"]["behavioral_observations"][
                "final_explicitly_identifies_version_2"
            ]
        )
        broken = copy.deepcopy(result)
        broken["final_tool_state"]["release_note"]["version"] = 1
        self.assertFalse(tool_runner.evaluate_control(broken)["score"]["passed"])

    def test_exact_argument_comparison(self):
        good = {
            "case_id": "02_obvious_weather",
            "calls": [{
                "name": "get_weather",
                "arguments": {"location": "Boston", "unit": "celsius"},
            }],
        }
        self.assertTrue(tool_runner.strict_calls_match(good))
        good["calls"][0]["arguments"]["unit"] = "fahrenheit"
        self.assertFalse(tool_runner.strict_calls_match(good))

    def test_targeted_case_exit_code_tracks_evaluation_and_errors(self):
        self.assertEqual(
            tool_runner.targeted_case_exit_code(
                {"error": None, "score": {"passed": True}}
            ),
            0,
        )
        self.assertEqual(
            tool_runner.targeted_case_exit_code(
                {"error": None, "score": {"passed": False}}
            ),
            1,
        )
        self.assertEqual(
            tool_runner.targeted_case_exit_code(
                {"error": "endpoint failed", "score": {"passed": False}}
            ),
            2,
        )

    def test_targeted_case_cli_returns_nonzero_on_failure_and_error(self):
        cases = (
            (
                {
                    "case_id": "02_obvious_weather",
                    "final": "wrong",
                    "calls": [],
                    "error": None,
                },
                1,
            ),
            (
                {
                    "case_id": "02_obvious_weather",
                    "final": "",
                    "calls": [],
                    "error": "endpoint failed",
                },
                2,
            ),
        )
        for index, (result, expected) in enumerate(cases):
            with self.subTest(
                expected=expected
            ), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / f"targeted-{index}"
                argv = [
                    "run-tools.py",
                    "--only-case",
                    "02_obvious_weather",
                    "--output-dir",
                    str(output),
                    "--runtime",
                    "test-runtime",
                ]
                with mock.patch.object(sys, "argv", argv), mock.patch.object(
                    tool_runner, "run_conversation", return_value=copy.deepcopy(result)
                ):
                    self.assertEqual(tool_runner.main(), expected)

    def test_safe_replay_scores_30_of_30(self):
        result = tool_runner.score_rows(copy.deepcopy(self.rows))
        self.assertTrue(result["gate_passed"])
        self.assertTrue(result["schedule_integrity"]["passed"])
        self.assertEqual(result["exact_tool_selection_and_arguments"], 30)
        self.assertFalse(result["external_side_effects_executed"])

    def test_thirty_copies_of_one_passing_row_are_rejected(self):
        rows = [copy.deepcopy(self.rows[0]) for _ in range(30)]
        result = self.assert_plan_rejected(rows)
        self.assertTrue(result["schedule_integrity"]["missing_identities"])
        self.assertTrue(result["schedule_integrity"]["unexpected_identities"])

    def test_replacing_required_row_with_duplicate_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[5] = copy.deepcopy(rows[0])
        self.assert_plan_rejected(rows)

    def test_omitted_invocation_is_rejected(self):
        self.assert_plan_rejected(copy.deepcopy(self.rows[:-1]))

    def test_extra_invocation_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows.append(copy.deepcopy(rows[-1]))
        self.assert_plan_rejected(rows)

    def test_wrong_phase_or_repeat_is_rejected(self):
        for field, value in (("phase", "smoke"), ("repeat", 99)):
            with self.subTest(field=field):
                rows = copy.deepcopy(self.rows)
                rows[4][field] = value
                self.assert_plan_rejected(rows)

    def test_boolean_repeats_are_rejected(self):
        for index, value in ((2, False), (1, True)):
            with self.subTest(value=value):
                rows = copy.deepcopy(self.rows)
                rows[index]["repeat"] = value
                result = self.assert_plan_rejected(rows)
                mismatch = result["schedule_integrity"]["mismatches"][0]
                self.assertEqual(mismatch["actual_repeat_type"], "bool")

    def test_integral_float_repeats_are_rejected(self):
        for index, value in ((2, 0.0), (1, 1.0)):
            with self.subTest(value=value):
                rows = copy.deepcopy(self.rows)
                rows[index]["repeat"] = value
                result = self.assert_plan_rejected(rows)
                mismatch = result["schedule_integrity"]["mismatches"][0]
                self.assertEqual(mismatch["actual_repeat_type"], "float")

    def test_none_is_allowed_only_at_canonical_none_positions(self):
        for index, value in ((2, None), (0, 0)):
            with self.subTest(index=index, value=value):
                rows = copy.deepcopy(self.rows)
                rows[index]["repeat"] = value
                self.assert_plan_rejected(rows)

    def test_reordered_invocations_are_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[2], rows[3] = rows[3], rows[2]
        self.assert_plan_rejected(rows)

    def test_malformed_replay_cli_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as temporary:
            replay = Path(temporary) / "incomplete.json"
            replay.write_text(json.dumps(self.rows[:-1]), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(ROOT / "run-tools.py"), "--replay", str(replay)],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(completed.returncode, 0)
        manifest = json.loads(completed.stdout)
        self.assertFalse(manifest["gate_passed"])
        self.assertFalse(manifest["schedule_integrity"]["passed"])

    def test_malformed_repeat_replay_cli_returns_nonzero(self):
        rows = copy.deepcopy(self.rows)
        rows[2]["repeat"] = False
        with tempfile.TemporaryDirectory() as temporary:
            replay = Path(temporary) / "boolean-repeat.json"
            replay.write_text(json.dumps(rows), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "run-tools.py"),
                    "--replay",
                    str(replay),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(completed.returncode, 0)
        manifest = json.loads(completed.stdout)
        self.assertFalse(manifest["gate_passed"])
        self.assertFalse(manifest["schedule_integrity"]["passed"])
        mismatch = manifest["schedule_integrity"]["mismatches"][0]
        self.assertEqual(mismatch["actual_repeat_type"], "bool")


class NeedleConstructionTests(unittest.TestCase):
    def test_locate_including_boundaries(self):
        self.assertEqual(needle_runner.locate([1, 2, 3, 4], [1, 2]), 0)
        self.assertEqual(needle_runner.locate([1, 2, 3, 4], [3, 4]), 2)
        self.assertIsNone(needle_runner.locate([1, 2, 3], [2, 4]))


class PublicationTests(unittest.TestCase):
    def test_httpx_live_dependency_is_declared(self):
        requirements = (ROOT.parent / "requirements.txt").read_text(
            encoding="utf-8"
        )
        self.assertRegex(requirements, r"(?m)^httpx(?:[<>=].*)?$")

    def test_public_markdown_local_links_resolve(self):
        repository = ROOT.parent
        checked = 0
        for markdown in repository.rglob("*.md"):
            text = markdown.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                local = target.split("#", 1)[0]
                if not local:
                    continue
                checked += 1
                self.assertTrue(
                    (markdown.parent / local).exists(),
                    f"broken link in {markdown}: {target}",
                )
        self.assertGreater(checked, 0)

    def test_validation_tree_has_no_host_evidence_paths_or_credentials(self):
        forbidden = (
            "/home/" + "mrkaos",
            "/opt/" + "ai-artifacts",
            "/srv/" + "models",
            "gh" + "o_",
            "192." + "168.",
        )
        for path in ROOT.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            for value in forbidden:
                self.assertNotIn(value, text, f"private value in {path}")


if __name__ == "__main__":
    unittest.main()
