#!/usr/bin/env python3
"""Non-inference structural checks for the public validation repository."""

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def check_json() -> list[str]:
    errors = []
    for path in ROOT.rglob("*.json"):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid JSON: {path.relative_to(ROOT)}: {exc}")
    for path in ROOT.rglob("*.jsonl"):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        ):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except Exception as exc:
                errors.append(
                    f"invalid JSONL: {path.relative_to(ROOT)}:{line_number}: {exc}"
                )
    return errors


def check_links() -> list[str]:
    errors = []
    pattern = re.compile(r"\[[^]]+\]\(([^)]+)\)")
    for path in ROOT.rglob("*.md"):
        if ".git" in path.parts:
            continue
        for target in pattern.findall(path.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            local = target.split("#", 1)[0]
            if local and not (path.parent / local).exists():
                errors.append(
                    f"broken link: {path.relative_to(ROOT)} -> {target}"
                )
    return errors


def check_case_contracts() -> list[str]:
    errors = []
    suite = json.loads(
        (ROOT / "validation/cases/tools.json").read_text(encoding="utf-8")
    )
    expectations = json.loads(
        (ROOT / "validation/cases/tool-expectations.json").read_text(
            encoding="utf-8"
        )
    )
    cases = suite["ordinary_cases"] + suite["concurrent_cases"]
    ids = [case["id"] for case in cases]
    expected_ids = list(expectations["cases"])
    if ids != expected_ids:
        errors.append(
            "tool case order differs from exact expectation manifest: "
            f"{ids!r} != {expected_ids!r}"
        )
    if suite["identity"]["expected_invocations"] != 30:
        errors.append("current tool suite expected_invocations is not 30")
    reasoning_text = (
        ROOT / "validation/cases/reasoning.py"
    ).read_text(encoding="utf-8")
    reasoning_ids = re.findall(r'"id": "(C[1-8])"', reasoning_text)
    if reasoning_ids != [f"C{index}" for index in range(1, 9)]:
        errors.append(f"unexpected reasoning case identity/order: {reasoning_ids}")
    return errors


def check_curated_runs() -> list[str]:
    errors = []
    payload = json.loads((ROOT / "results/runs.json").read_text(encoding="utf-8"))
    runs = payload.get("runs", [])
    ids = [run.get("id") for run in runs]
    if len(ids) != len(set(ids)):
        errors.append("duplicate curated run id")
    required = {
        "id",
        "date",
        "model",
        "runtime",
        "runtime_commit",
        "hardware",
        "launch_shape",
        "weight_format",
        "target_kv",
        "context_admission_tokens",
        "suite_commit",
        "evidence_roots",
        "evidence_gaps",
        "comparability",
    }
    for run in runs:
        missing = sorted(required - set(run))
        if missing:
            errors.append(f"{run.get('id', '<unknown>')} missing: {missing}")
    return errors


def main() -> int:
    errors = []
    errors.extend(check_json())
    errors.extend(check_links())
    errors.extend(check_case_contracts())
    errors.extend(check_curated_runs())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("repository validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
