"""Verify calibrated hit filtering against the frozen development retrieval set."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.knowledge.hybrid import (  # noqa: E402
    RELEVANCE_FLOORS,
    RELEVANCE_REVISION,
    search,
)

INDEX = ROOT / "data/indexes/hybrid.sqlite3"
EVAL = ROOT / "evals/ceres2-optimization-retrieval-dev.json"
OUTPUT = Path(__file__).with_name("relevance-hits-smoke-v2-2026-10-07.json")


def main() -> None:
    evaluation_bytes = EVAL.read_bytes()
    evaluation = json.loads(evaluation_bytes)
    results = []
    failures = []
    for case in evaluation["cases"]:
        result = search(INDEX, case["query"], case["namespace"], limit=10)
        hits = result["hits"]
        target_ids = case["target_ids"]
        top3_ids = {hit["id"] for hit in hits[:3]}
        hit_ids = {hit["id"] for hit in hits}
        excluded_ids = case.get("excluded_ids", [])
        positive_top3 = all(identity in top3_ids for identity in target_ids)
        negative_empty = bool(target_ids) or not hits
        excluded_filtered = not (set(excluded_ids) & hit_ids)
        if not positive_top3:
            failures.append({"case_id": case["id"], "reason": "target_missing_from_hits_top3"})
        if not negative_empty:
            failures.append({"case_id": case["id"], "reason": "negative_has_hits"})
        if not excluded_filtered:
            failures.append({"case_id": case["id"], "reason": "excluded_id_in_hits"})
        results.append({
            "case_id": case["id"],
            "namespace": case["namespace"],
            "query": case["query"],
            "target_ids": target_ids,
            "target_hit_ranks": {
                identity: next((i for i, hit in enumerate(hits, 1) if hit["id"] == identity), None)
                for identity in target_ids
            },
            "hits_top3": [
                {"id": hit["id"], "rrf_score": hit["rrf_score"], "cosine": hit["scores"].get("dense")}
                for hit in hits[:3]
            ],
            "hit_count": len(hits),
            "negative_empty": negative_empty,
            "excluded_ids": excluded_ids,
            "excluded_hit_ids": sorted(set(excluded_ids) & hit_ids),
            "relevance_floor": result["relevance_floor"],
            "positive_targets_top3": positive_top3,
        })

    import sqlite3

    with sqlite3.connect(f"file:{INDEX}?mode=ro", uri=True) as db:
        manifest = json.loads(db.execute("SELECT content FROM manifest").fetchone()[0])
    expected_hash = hashlib.sha256(evaluation_bytes).hexdigest()
    assert manifest["relevance_revision"] == RELEVANCE_REVISION
    assert manifest["relevance_floors"] == RELEVANCE_FLOORS
    assert manifest["calibration_sha256"] == expected_hash

    report = {
        "eval_version": evaluation["version"],
        "purpose": evaluation["purpose"],
        "index_manifest": {
            "relevance_revision": manifest["relevance_revision"],
            "relevance_floors": manifest["relevance_floors"],
            "calibration_sha256": manifest["calibration_sha256"],
            "expected_calibration_sha256": expected_hash,
        },
        "case_count": len(results),
        "positive_case_count": sum(bool(case["target_ids"]) for case in evaluation["cases"]),
        "negative_case_count": sum(not case["target_ids"] for case in evaluation["cases"]),
        "positive_targets_top3_count": sum(row["positive_targets_top3"] for row in results if row["target_ids"]),
        "negative_empty_count": sum(row["negative_empty"] for row in results if not row["target_ids"]),
        "potato_chips_excluded_from_hits": all(
            row["excluded_hit_ids"] == [] for row in results if row["excluded_ids"]
        ),
        "failures": failures,
        "cases": results,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in (
        "eval_version", "case_count", "positive_case_count", "negative_case_count",
        "positive_targets_top3_count", "negative_empty_count",
        "potato_chips_excluded_from_hits", "failures", "index_manifest",
    )}, ensure_ascii=False, indent=2))
    assert not failures, failures


if __name__ == "__main__":
    main()
