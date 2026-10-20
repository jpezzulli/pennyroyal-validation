#!/usr/bin/env python3
"""Validate and aggregate a blinded frozen-suite grading file."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CASE_METADATA_FIELDS = frozenset({"note", "deduction_justifications"})
REVISION_CASE_ID = "C8"
REVISION_DIMENSION = "revision_quality"
MAX_DIMENSION_SCORE = 4
LOOP_BEHAVIOR_DIMENSION = "loop_behavior"
FINAL_ANSWER_USABILITY_DIMENSION = "final_answer_usability"
GENUINE_LOOP_CAP = "confirmed_reasoning_loop"
EXHAUSTION_CAP = "repetitive_32768_exhaustion_without_usable_answer"
MISSING_ANSWER_CATEGORY = "missing_or_unusable_final_answer"
LEGACY_LOOP_POLICY_LABEL = "legacy-loop-efficiency-superseded"
POLICY_HINT = "re-score grades locked before this correction with --legacy-loop-policy"


def load_python(path: Path):
    spec = importlib.util.spec_from_file_location("reasoning_cases", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def expected_case_dimensions(case_id: str, rubric: dict) -> set[str]:
    """Derive the complete dimension schema from the frozen rubric."""
    dimensions = set(rubric["dimension_weights"])
    if REVISION_DIMENSION not in dimensions:
        raise ValueError(
            f"rubric is missing required dimension {REVISION_DIMENSION}"
        )
    if case_id == REVISION_CASE_ID:
        return dimensions
    return dimensions - {REVISION_DIMENSION}


def loop_policy_of(rubric: dict) -> dict:
    """Return the rubric's genuine-loop-only policy, or fail closed."""
    policy = rubric.get("loop_policy")
    if not isinstance(policy, dict):
        raise ValueError(
            "rubric declares no loop_policy; the corrected contract requires "
            f"one ({POLICY_HINT})"
        )
    missing = [
        name
        for name in ("substantive_defect_categories", "genuine_loop_categories")
        if not policy.get(name)
    ]
    if missing:
        raise ValueError(
            f"rubric loop_policy is incomplete: missing={missing} ({POLICY_HINT})"
        )
    return policy


def validate_deduction_evidence(grade: dict, rubric: dict) -> None:
    """Require a named, quoted, same-case defect for every deduction and cap.

    Repetition, extended xhigh deliberation, verbosity, long traces, similarity
    flags, and output length or an output cap are not quality defects. Every
    dimension scored below full credit must therefore record a defect category
    and quoted evidence. A docked ``loop_behavior`` may only cite a genuine-loop
    category, because an answer defect never lowers loop behavior; a genuine-loop
    category may only dock ``loop_behavior``, because looping must not be
    relabeled as a defect in another dimension. Guarded fatal caps must name an
    existing case and be supported by that same case's docked dimension, so an
    unrelated annotation cannot launder an unsupported failure.
    """
    policy = loop_policy_of(rubric)
    substantive = frozenset(policy["substantive_defect_categories"])
    genuine = frozenset(policy["genuine_loop_categories"])
    non_detractors = frozenset(policy.get("non_detractors", ()))
    field = policy.get("justification_field", "deduction_justifications")
    cap_support = {
        GENUINE_LOOP_CAP: (LOOP_BEHAVIOR_DIMENSION, genuine),
        EXHAUSTION_CAP: (
            FINAL_ANSWER_USABILITY_DIMENSION,
            frozenset({MISSING_ANSWER_CATEGORY}),
        ),
    }
    scores = grade.get("cases") or {}
    evidenced: dict[str, dict[str, str]] = {}

    for case_id in sorted(scores):
        case_grade = scores[case_id]
        entries = case_grade.get(field)
        if entries is None:
            entries = {}
        if not isinstance(entries, dict):
            raise ValueError(f"{case_id} {field} must be an object")

        docked = {
            name
            for name, value in case_grade.items()
            if name not in CASE_METADATA_FIELDS
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
            and value < MAX_DIMENSION_SCORE
        }
        unexplained = sorted(docked - set(entries))
        if unexplained:
            raise ValueError(
                f"{case_id} docked {unexplained} with no recorded defect category "
                "and quoted evidence; repetition, verbosity, long traces, "
                "similarity flags, and output caps alone are not deductions "
                f"({POLICY_HINT})"
            )

        for dimension, entry in sorted(entries.items()):
            if dimension not in rubric["dimension_weights"]:
                raise ValueError(
                    f"{case_id}.{field}.{dimension} is not a rubric dimension"
                )
            if not isinstance(entry, dict):
                raise ValueError(f"{case_id}.{field}.{dimension} must be an object")
            category = entry.get("category")
            evidence = entry.get("evidence")
            if not isinstance(evidence, str) or not evidence.strip():
                raise ValueError(
                    f"{case_id}.{dimension} deduction requires non-empty quoted "
                    "evidence of the defect"
                )
            if dimension not in docked:
                raise ValueError(
                    f"{case_id}.{dimension} cites {category!r} but the dimension "
                    "keeps full credit; a justification may only accompany a "
                    "deduction"
                )
            if category in non_detractors:
                raise ValueError(
                    f"{case_id}.{dimension} cites a non-detractor: {category!r} is "
                    "repetition, verbosity, length, reconsideration, a similarity "
                    "flag, or an output cap, not a demonstrated defect"
                )
            if dimension == LOOP_BEHAVIOR_DIMENSION:
                if category not in genuine:
                    raise ValueError(
                        f"{case_id}.loop_behavior may only be docked for a "
                        f"genuine-loop category {sorted(genuine)}; answer defects "
                        "belong in their own dimension"
                    )
            elif category in genuine:
                raise ValueError(
                    f"{case_id}.{dimension} cites loop category {category!r}; "
                    "genuine looping is charged only through loop_behavior"
                )
            elif category not in substantive:
                raise ValueError(
                    f"{case_id}.{dimension} deduction category {category!r} is not "
                    f"a substantive defect category: {sorted(substantive)}"
                )
            evidenced.setdefault(case_id, {})[dimension] = category

    for finding in grade.get("fatal_findings") or []:
        cap_name = finding.get("cap")
        if cap_name not in cap_support:
            continue
        dimension, categories = cap_support[cap_name]
        finding_case = finding.get("case_id")
        if not isinstance(finding_case, str) or finding_case not in scores:
            raise ValueError(
                f"fatal cap {cap_name} must carry the case_id it applies to; "
                f"got {finding_case!r}"
            )
        category = evidenced.get(finding_case, {}).get(dimension)
        if category is None:
            raise ValueError(
                f"fatal cap {cap_name} requires case {finding_case} to dock "
                f"{dimension} with quoted evidence; a similarity flag, token "
                "count, or output cap alone is not confirmation of looping"
            )
        if category not in categories:
            raise ValueError(
                f"fatal cap {cap_name} requires case {finding_case} {dimension} "
                f"to cite {sorted(categories)}, not {category!r}"
            )


def score_grade(
    grade: dict,
    cases: list[dict],
    rubric: dict,
    legacy_loop_policy: bool = False,
) -> dict:
    case_map = {case["id"]: case for case in cases}
    scores = grade.get("cases") or {}
    if set(scores) != set(case_map):
        raise ValueError("grade must contain exactly C1-C8")

    dimension_weights = rubric["dimension_weights"]
    dimension_averages = {}
    case_scores = {}
    for case_id, case_grade in scores.items():
        expected = expected_case_dimensions(case_id, rubric)
        supplied = set(case_grade) - CASE_METADATA_FIELDS
        missing = sorted(expected - supplied)
        unexpected = sorted(supplied - expected)
        if missing or unexpected:
            details = []
            if missing:
                details.append(f"missing={missing}")
            if unexpected:
                details.append(f"unexpected={unexpected}")
            raise ValueError(
                f"{case_id} dimension schema mismatch: {'; '.join(details)}"
            )
        applicable = {name: case_grade[name] for name in expected}
        for name, value in applicable.items():
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0 <= value <= 4
            ):
                raise ValueError(f"{case_id}.{name} must be between 0 and 4")
        total_weight = sum(dimension_weights[name] for name in applicable)
        case_scores[case_id] = 100 * sum(
            value * dimension_weights[name] for name, value in applicable.items()
        ) / (4 * total_weight)

    for dimension in dimension_weights:
        participating = [
            (case_map[case_id]["weight"], case_grade[dimension])
            for case_id, case_grade in scores.items()
            if dimension in case_grade
        ]
        if not participating:
            raise ValueError(f"dimension {dimension} has no scores")
        dimension_averages[dimension] = sum(
            weight * value for weight, value in participating
        ) / sum(weight for weight, _ in participating)

    qualitative = sum(
        dimension_averages[name] * weight
        for name, weight in dimension_weights.items()
    ) / (4 * sum(dimension_weights.values())) * 100

    if legacy_loop_policy:
        loop_policy = LEGACY_LOOP_POLICY_LABEL
    else:
        validate_deduction_evidence(grade, rubric)
        loop_policy = loop_policy_of(rubric).get("version", "unversioned")

    fatal_findings = grade.get("fatal_findings") or []
    capped = qualitative
    for finding in fatal_findings:
        cap_name = finding.get("cap")
        if cap_name not in rubric["fatal_caps"]:
            raise ValueError(f"unknown fatal cap: {cap_name}")
        capped = min(capped, rubric["fatal_caps"][cap_name])

    return {
        "case_scores": {key: round(value, 4) for key, value in case_scores.items()},
        "dimension_averages": {
            key: round(value, 4) for key, value in dimension_averages.items()
        },
        "qualitative_score": round(qualitative, 4),
        "loop_policy": loop_policy,
        "fatal_findings": fatal_findings,
        "final_score": round(capped, 4),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate a completed blinded grade for the frozen reasoning suite."
    )
    parser.add_argument("--grade", type=Path, required=True)
    parser.add_argument("--cases", type=Path, default=ROOT / "cases/reasoning.py")
    parser.add_argument(
        "--rubric", type=Path, default=ROOT / "cases/reasoning-rubric.json"
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--legacy-loop-policy",
        action="store_true",
        help=(
            "Skip the genuine-loop-only deduction checks when re-scoring a grade "
            "locked before that correction; archived numbers are never rewritten."
        ),
    )
    args = parser.parse_args()

    cases = load_python(args.cases).CASES
    rubric = json.loads(args.rubric.read_text(encoding="utf-8"))
    grade = json.loads(args.grade.read_text(encoding="utf-8"))
    result = score_grade(
        grade, cases, rubric, legacy_loop_policy=args.legacy_loop_policy
    )
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
