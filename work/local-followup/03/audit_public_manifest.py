#!/usr/bin/env python3
"""Metadata-only audit of the public Ceres2 local-followup development set."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ALLOWED_OPERATORS = {"eq", "contains", "min", "max", "length", "min_length"}
ALLOWED_STEP_OPS = {"confirm_plan", "repeat_confirmation", "turn"}
REQUIRED_CASE_KEYS = {
    "case_id", "message", "category", "scenario_family", "split", "core",
    "expected_behavior", "fact_sources", "checks",
}


def pointer_exists(repo: Path, pointer: str) -> bool:
    source_name, anchor = pointer.split("#", 1)
    source = repo / source_name
    if not source.is_file():
        return False
    text = source.read_text(encoding="utf-8")
    if anchor in text:
        return True
    if source.suffix != ".json":
        return False
    value = json.loads(text)
    for part in anchor.split("."):
        if not isinstance(value, dict) or part not in value:
            return False
        value = value[part]
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cases", type=Path,
        default=Path(__file__).resolve().parents[3] / "evals" / "ceres2-local-followup-dev.json",
    )
    args = parser.parse_args()
    case_path = args.cases.resolve()
    repo = case_path.parents[1]
    data = json.loads(case_path.read_text(encoding="utf-8"))
    cases = data["cases"]
    errors: list[str] = []

    if data["schema_version"] != "ceres-local-followup-dev-cases-v1":
        errors.append("unexpected schema_version")
    if len(cases) != 40 or len({case["case_id"] for case in cases}) != 40:
        errors.append("expected 40 unique public regression cases")
    if sum(case["core"] is True for case in cases) != 20:
        errors.append("expected 20 core cases")
    if any(case["split"] != "regression" for case in cases):
        errors.append("non-regression case found in public set")
    if len({case["scenario_family"] for case in cases}) != len(cases):
        errors.append("public scenario_family values are not unique")

    source_count = 0
    invalid_sources: list[str] = []
    operator_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    path_counts: Counter[str] = Counter()
    step_counts: Counter[str] = Counter()
    categories: Counter[str] = Counter()

    for case in cases:
        categories[case["category"]] += 1
        keys = set(case)
        if not REQUIRED_CASE_KEYS <= keys <= REQUIRED_CASE_KEYS | {"steps"}:
            errors.append(f"invalid case keys: {case['case_id']}")
        if not case["message"] or not case["expected_behavior"] or not case["fact_sources"]:
            errors.append(f"empty required case content: {case['case_id']}")
        for pointer in case["fact_sources"]:
            source_count += 1
            try:
                valid = pointer_exists(repo, pointer)
            except (ValueError, json.JSONDecodeError):
                valid = False
            if not valid:
                invalid_sources.append(pointer)
        for check in case["checks"]:
            if set(check) != {"expected", "operator", "path"}:
                errors.append(f"invalid check keys: {case['case_id']}")
            if check["operator"] not in ALLOWED_OPERATORS:
                errors.append(f"invalid check operator: {case['case_id']}")
            operator_counts[check["operator"]] += 1
            path_counts[check["path"]] += 1
            if check["path"] in {"capture.status", "outcome", "navigation.status"}:
                status_counts[f"{check['path']}={check['expected']}"] += 1
        for step in case.get("steps", []):
            op = step.get("op")
            step_counts[op] += 1
            valid_turn = op == "turn" and set(step) == {"op", "message"} and bool(step["message"])
            valid_action = op in {"confirm_plan", "repeat_confirmation"} and set(step) == {"op"}
            if op not in ALLOWED_STEP_OPS or not (valid_turn or valid_action):
                errors.append(f"invalid step shape: {case['case_id']}")

    if invalid_sources:
        errors.extend(f"unresolved source pointer: {pointer}" for pointer in invalid_sources)

    report = {
        "version": data["version"],
        "schema_version": data["schema_version"],
        "case_count": len(cases),
        "core_count": sum(case["core"] is True for case in cases),
        "scenario_family_count": len({case["scenario_family"] for case in cases}),
        "categories": dict(sorted(categories.items())),
        "fact_pointer_count": source_count,
        "unresolved_fact_pointer_count": len(invalid_sources),
        "operator_counts": dict(sorted(operator_counts.items())),
        "status_expectation_counts": dict(sorted(status_counts.items())),
        "step_operation_counts": dict(sorted(step_counts.items())),
        "check_path_counts": dict(sorted(path_counts.items())),
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
