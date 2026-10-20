#!/usr/bin/env python3
"""Build text-only grading packets, excluding all operational metadata."""

import argparse
import importlib.util
import json
from pathlib import Path


def load_suite(path):
    spec = importlib.util.spec_from_file_location("frozen_suite", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grading_guidance(rubric):
    """Return the grading contract carried by every exported packet."""
    policy = rubric.get("loop_policy") or {}
    field = policy.get("justification_field", "deduction_justifications")
    return {
        "scale": rubric.get("scale"),
        "loop_policy": policy,
        "required_justification_field": field,
        "loop_penalties": (
            "Repetition, extended or revisited deliberation, verbosity, long "
            "reasoning traces, semantic-similarity flags, and output length or "
            "cap exhaustion are not deductions on their own. Every dimension "
            "scored below 4 must record a defect category and quoted evidence "
            f"in {field}. loop_behavior may be docked only for a genuine-loop "
            "category; substantive answer defects belong in their own "
            "dimension. Incorrect conclusions, unsupported claims, missed "
            "explicit requirements, and failed corrections remain assessable. "
            "A guarded cap must carry the case_id it applies to and be supported "
            "by that same case's docked dimension: loop_behavior for a "
            "genuine-loop category, final_answer_usability for "
            "missing_or_unusable_final_answer."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--rubric",
        default=str(
            Path(__file__).resolve().parents[1] / "design/rubric.json"
        ),
    )
    args = parser.parse_args()
    suite = load_suite(Path(args.suite))
    guidance = grading_guidance(json.loads(Path(args.rubric).read_text()))
    cases = {case["id"]: case for case in suite.CASES}
    results = [
        json.loads(line) for line in Path(args.results).read_text().splitlines()
        if line.strip()
    ]
    measured = [item for item in results if item.get("kind") == "measured"]
    by_case = {}
    for item in measured:
        by_case.setdefault(item["case_id"], {})[item["turn"]] = item
    packets = []
    for index, case_id in enumerate(suite.CASE_ORDER, start=1):
        case = cases[case_id]
        turns = by_case.get(case_id, {})
        first = turns.get(1, {})
        transcript = [
            {"role": "system", "content": suite.SYSTEM},
            {"role": "user", "content": case["prompt"]},
            {
                "role": "assistant",
                "reasoning_content": first.get("reasoning_content", ""),
                "content": first.get("content", ""),
            },
        ]
        if case_id == "C8":
            second = turns.get(2, {})
            transcript.extend([
                {"role": "user", "content": case["correction"]},
                {
                    "role": "assistant",
                    "reasoning_content": second.get("reasoning_content", ""),
                    "content": second.get("content", ""),
                },
            ])
        packets.append({
            "candidate_id": "candidate-7f3a",
            "run_id": f"screen-{index:02d}",
            "case_id": case_id,
            "transcript": transcript,
            "grading_guidance": guidance,
        })
    Path(args.output).write_text(
        json.dumps(packets, indent=2, ensure_ascii=False) + "\n"
    )


if __name__ == "__main__":
    main()

