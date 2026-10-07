"""Technical-only smoke for explicit labels and their failure boundaries."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TMP = Path(__file__).resolve().parent / "tmp" / "annotation-contract"
TMP.mkdir(parents=True, exist_ok=True)

import sys

sys.path.insert(0, str(ROOT / "backend"))

from app.evaluation.annotate_runs import annotate  # noqa: E402
from pydantic import ValidationError  # noqa: E402


CAPTURE = ROOT / "data/generated/evals/pi-real-provider-recipe-relations-capture-2026-10-07.jsonl"
PRESERVED_FIELDS = ("export_source_snapshot", "events", "observed_usage")


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records))


def expects_exception(call, error_type: type[Exception]) -> bool:
    try:
        call()
    except error_type:
        return True
    return False


def main() -> None:
    actual = [json.loads(line) for line in CAPTURE.read_text().splitlines() if line.strip()]
    if not actual:
        raise AssertionError("The actual provider export has no run to use for this technical smoke")
    tagged = deepcopy(actual[0])
    untagged = deepcopy(actual[0])
    untagged["run_id"] = "synthetic-untagged-technical-fixture"
    captures = TMP / "captures.jsonl"
    annotations = TMP / "annotations.jsonl"
    output = TMP / "reviewed.jsonl"
    fixture_rows = [tagged, untagged]
    write_jsonl(captures, fixture_rows)
    label = {
        "run_id": tagged["run_id"],
        "verdict": "needs_review",
        "error_type": "technical_smoke",
        "severity": "none",
        "expected_behavior": "Verify that explicitly supplied labels join only to their matching run.",
        "rationale": "Synthetic schema test only; this is not a human review or product-quality judgment.",
        "reviewer": "synthetic-technical-smoke",
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    write_jsonl(annotations, [label])
    summary = annotate(captures, annotations, output)
    reviewed = [json.loads(line) for line in output.read_text().splitlines() if line.strip()]
    label_join_correct = (
        summary["records"] == 2
        and summary["annotated"] == 1
        and reviewed[0]["labels"]["reviewer"] == "synthetic-technical-smoke"
        and reviewed[1]["labels"] is None
    )
    source_event_usage_preserved = all(
        before.get(field) == after.get(field)
        for before, after in zip(fixture_rows, reviewed, strict=True)
        for field in PRESERVED_FIELDS
    )
    event_timestamps_are_separate_fields = all(
        "recorded_at_ms" in event and "elapsed_ms" in event
        for event in reviewed[0].get("events", [])
    )

    unknown_annotations = TMP / "unknown.jsonl"
    write_jsonl(unknown_annotations, [{**label, "run_id": "unknown-run-technical-fixture"}])
    unknown_run_rejected = expects_exception(
        lambda: annotate(captures, unknown_annotations, TMP / "unknown-output.jsonl"), KeyError
    )

    duplicate_annotations = TMP / "duplicate.jsonl"
    write_jsonl(duplicate_annotations, [label, label])
    duplicate_run_rejected = expects_exception(
        lambda: annotate(captures, duplicate_annotations, TMP / "duplicate-output.jsonl"), ValueError
    )

    invalid_annotations = TMP / "invalid.jsonl"
    write_jsonl(invalid_annotations, [{**label, "unexpected_field": "reject"}])
    invalid_field_rejected = expects_exception(
        lambda: annotate(captures, invalid_annotations, TMP / "invalid-output.jsonl"), ValidationError
    )

    result = {
        "actual_provider_capture_used_as_source": True,
        "fixture_rows_for_join_contract": 2,
        "second_row_is_explicit_synthetic_unannotated_fixture": True,
        "label_join_correct": label_join_correct,
        "unannotated_row_remains_null": reviewed[1]["labels"] is None,
        "source_events_usage_preserved": source_event_usage_preserved,
        "event_timestamps_are_separate_fields": event_timestamps_are_separate_fields,
        "unknown_run_rejected": unknown_run_rejected,
        "duplicate_run_rejected": duplicate_run_rejected,
        "invalid_annotation_field_rejected": invalid_field_rejected,
        "synthetic_label_is_not_a_human_review": True,
        "owner_or_run_id_written_to_report": False,
    }
    assert all(
        result[key]
        for key in (
            "label_join_correct",
            "source_events_usage_preserved",
            "event_timestamps_are_separate_fields",
            "unknown_run_rejected",
            "duplicate_run_rejected",
            "invalid_annotation_field_rejected",
        )
    ), result
    report = Path(__file__).resolve().parent / "annotation-contract-smoke-current-2026-10-07.json"
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
