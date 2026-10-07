"""Sample sparse, dense, and RRF rankings for the versioned dev set."""

from __future__ import annotations

import json
import math
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.knowledge.hybrid import RELEVANCE_FLOORS, search  # noqa: E402


INDEX = ROOT / "data" / "indexes" / "hybrid.sqlite3"
EVAL_PATH = ROOT / "evals" / "ceres2-optimization-retrieval-dev.json"
OUTPUT_PATH = Path(__file__).with_name("retrieval-dev-run-v4-literal-or-dense-2026-10-07.json")
HITS_OUTPUT_PATH = Path(__file__).with_name("relevance-hits-smoke-v4-literal-or-dense-2026-10-07.json")


def candidate_ids(rows: list[tuple[str, float]], limit: int) -> list[dict]:
    return [{"id": identity, "score": score} for identity, score in rows[:limit]]


def main() -> None:
    evaluation = json.loads(EVAL_PATH.read_text())
    with sqlite3.connect(f"file:{INDEX}?mode=ro", uri=True) as db:
        indexed_ids = {
            namespace: {
                row[0]
                for row in db.execute(
                    "SELECT id FROM documents WHERE namespace = ?", (namespace,)
                )
            }
            for namespace in ("recipe", "product", "policy")
        }

    results = []
    hit_cases = []
    hit_failures = []
    index_manifest = None
    positive_scores: dict[str, list[dict]] = defaultdict(list)
    negative_maxima: dict[str, list[dict]] = defaultdict(list)
    for case in evaluation["cases"]:
        namespace = case["namespace"]
        result = search(INDEX, case["query"], namespace, limit=1000)
        index_manifest = result["manifest"]
        sparse = result["sparse"]
        dense = result["dense"]
        fused = result["candidates"]
        hits = result["hits"]
        dense_by_id = dict(dense)
        sparse_rank = {identity: rank for rank, (identity, _) in enumerate(sparse, 1)}
        dense_rank = {identity: rank for rank, (identity, _) in enumerate(dense, 1)}
        fused_rank = {item["id"]: rank for rank, item in enumerate(fused, 1)}
        hit_rank = {item["id"]: rank for rank, item in enumerate(hits, 1)}
        for hit in fused:
            expected_score = sum(1 / (60 + rank) for rank in hit["ranks"].values())
            assert math.isclose(hit["rrf_score"], expected_score, rel_tol=0, abs_tol=1e-15)

        targets = case["target_ids"]
        missing_targets = [identity for identity in targets if identity not in indexed_ids[namespace]]
        assert not missing_targets, (case["id"], missing_targets)
        target_scores = {identity: dense_by_id[identity] for identity in targets}
        if targets:
            positive_scores[namespace].extend(
                {"case_id": case["id"], "target_id": identity, "cosine": score}
                for identity, score in target_scores.items()
            )
        else:
            negative_maxima[namespace].append({
                "case_id": case["id"],
                "query": case["query"],
                "max_cosine": dense[0][1],
                "top_id": dense[0][0],
            })

        excluded = case.get("excluded_ids", [])
        target_hit_ranks = {identity: hit_rank.get(identity) for identity in targets}
        positive_targets_top3 = all(rank is not None and rank <= 3 for rank in target_hit_ranks.values())
        negative_empty = bool(targets) or not hits
        excluded_hit_ids = sorted(set(excluded) & {item["id"] for item in hits})
        if targets and not positive_targets_top3:
            hit_failures.append({"case_id": case["id"], "reason": "target_missing_from_hits_top3"})
        if not targets and not negative_empty:
            hit_failures.append({"case_id": case["id"], "reason": "negative_has_hits"})
        if excluded_hit_ids:
            hit_failures.append({"case_id": case["id"], "reason": "excluded_id_in_hits", "ids": excluded_hit_ids})
        hit_cases.append({
            "case_id": case["id"],
            "namespace": namespace,
            "query": case["query"],
            "target_ids": targets,
            "target_hit_ranks": target_hit_ranks,
            "hits_top3": [
                {"id": item["id"], "rrf_score": item["rrf_score"], "cosine": item["scores"].get("dense")}
                for item in hits[:3]
            ],
            "hit_count": len(hits),
            "negative_empty": negative_empty,
            "excluded_ids": excluded,
            "excluded_hit_ids": excluded_hit_ids,
            "relevance_floor": result["relevance_floor"],
            "positive_targets_top3": positive_targets_top3,
        })
        results.append({
            "case_id": case["id"],
            "namespace": namespace,
            "query": case["query"],
            "target_ids": targets,
            "target_dense_scores": target_scores,
            "target_ranks": {
                identity: {
                    "sparse": sparse_rank.get(identity),
                    "dense": dense_rank.get(identity),
                    "rrf": fused_rank.get(identity),
                }
                for identity in targets
            },
            "top3": {
                "sparse": candidate_ids(sparse, 3),
                "dense": candidate_ids(dense, 3),
                "rrf": [
                    {"id": item["id"], "score": item["rrf_score"], "ranks": item["ranks"]}
                    for item in fused[:3]
                ],
            },
            "top10": {
                "sparse": candidate_ids(sparse, 10),
                "dense": candidate_ids(dense, 10),
                "rrf": [
                    {"id": item["id"], "score": item["rrf_score"], "ranks": item["ranks"]}
                    for item in fused[:10]
                ],
            },
            "hit_top3_ids": [item["id"] for item in hits[:3]],
            "hit_count": len(hits),
            "target_hit_ranks": target_hit_ranks,
            "positive_targets_top3": positive_targets_top3,
            "negative_empty": negative_empty,
            "excluded_hit_ids": excluded_hit_ids,
            "excluded_source_ranks": {
                identity: {
                    "sparse": sparse_rank.get(identity),
                    "dense": dense_rank.get(identity),
                    "rrf": fused_rank.get(identity),
                    "dense_cosine": dense_by_id.get(identity),
                }
                for identity in excluded
            },
            "sparse_count": len(sparse),
            "dense_count": len(dense),
            "rrf_count": len(fused),
            "rrf_formula_verified": True,
        })

    separability = {}
    for namespace in ("recipe", "product", "policy"):
        positives = positive_scores[namespace]
        negatives = negative_maxima[namespace]
        positive_min = min((row["cosine"] for row in positives), default=None)
        negative_max = max((row["max_cosine"] for row in negatives), default=None)
        separability[namespace] = {
            "positive_target_count": len(positives),
            "positive_min_target_cosine": positive_min,
            "positive_min_target": min(positives, key=lambda row: row["cosine"]) if positives else None,
            "negative_case_count": len(negatives),
            "negative_max_cosine": negative_max,
            "negative_max_case": max(negatives, key=lambda row: row["max_cosine"]) if negatives else None,
            "dense_scores_separable_on_this_dev_sample": (
                positive_min > negative_max if positive_min is not None and negative_max is not None else None
            ),
            "margin": positive_min - negative_max if positive_min is not None and negative_max is not None else None,
        }

    report = {
        "eval_version": evaluation["version"],
        "purpose": evaluation["purpose"],
        "model_id": "BAAI/bge-small-zh-v1.5",
        "model_revision": "7999e1d3359715c523056ef9478215996d62a620",
        "dense_comparison": "positive minimum target cosine vs negative query maximum cosine; no threshold selected",
        "namespace_dense_separability": separability,
        "cases": results,
        "hit_filter_validation": {
            "relevance_floors": RELEVANCE_FLOORS,
            "positive_case_count": sum(bool(case["target_ids"]) for case in evaluation["cases"]),
            "negative_case_count": sum(not case["target_ids"] for case in evaluation["cases"]),
            "positive_targets_top3_count": sum(row["positive_targets_top3"] for row in hit_cases if row["target_ids"]),
            "negative_empty_count": sum(row["negative_empty"] for row in hit_cases if not row["target_ids"]),
            "potato_chips_excluded_from_hits": all(not row["excluded_hit_ids"] for row in hit_cases if row["excluded_ids"]),
            "failures": hit_failures,
            "cases": hit_cases,
        },
    }
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    HITS_OUTPUT_PATH.write_text(json.dumps({
        "eval_version": report["eval_version"],
        "purpose": report["purpose"],
        "model_id": report["model_id"],
        "model_revision": report["model_revision"],
        "tokenizer_revision": index_manifest["tokenizer_revision"],
        "index_manifest": {
            "tokenizer_revision": index_manifest["tokenizer_revision"],
            "relevance_revision": index_manifest["relevance_revision"],
            "relevance_floors": index_manifest["relevance_floors"],
            "calibration_sha256": index_manifest["calibration_sha256"],
        },
        "validation": report["hit_filter_validation"],
    }, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "eval_version": report["eval_version"],
        "case_count": len(results),
        "model_id": report["model_id"],
        "model_revision": report["model_revision"],
        "namespace_dense_separability": separability,
        "hit_filter_validation": {
            key: value for key, value in report["hit_filter_validation"].items() if key != "cases"
        },
        "output_path": str(OUTPUT_PATH),
        "hits_output_path": str(HITS_OUTPUT_PATH),
    }, ensure_ascii=False, indent=2))
    assert not hit_failures, hit_failures


if __name__ == "__main__":
    main()
