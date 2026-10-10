#!/usr/bin/env python3
"""Score the public 18-query retrieval development report without reading holdout."""

import argparse
import hashlib
import json
import sqlite3
from collections import defaultdict
from pathlib import Path


LANES = ("bm25", "dense", "rrf")
TIMING_FIELDS = ("elapsed_ms", "wall_ms", "latency_ms", "duration_ms", "first_interim_ms")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lane_ids(row: dict, lane: str) -> list[str]:
    values = row["hits"] if lane == "rrf" else row["dense" if lane == "dense" else "sparse"]
    if lane == "rrf":
        return [str(value) for value in values]
    return [str(value[0]) for value in values]


def score(eval_path: Path, report_path: Path, index_path: Path) -> dict:
    evaluation = json.loads(eval_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report["eval_sha256"] != sha256(eval_path):
        raise ValueError("retrieval report was produced from a different evaluation source")
    expected = {case["id"]: case for case in evaluation["cases"]}
    observed = {row["case_id"]: row for row in report["cases"]}
    if len(expected) != len(evaluation["cases"]) or len(observed) != len(report["cases"]):
        raise ValueError("duplicate development case IDs")
    if set(expected) != set(observed):
        raise ValueError("report cases do not exactly match the public evaluation cases")

    canonical_by_namespace: dict[str, set[str]] = defaultdict(set)
    resolved_index = index_path.resolve()
    with sqlite3.connect(f"file:{resolved_index}?mode=ro", uri=True) as connection:
        for namespace, identity in connection.execute("SELECT namespace, id FROM documents"):
            canonical_by_namespace[namespace].add(identity)

    results = {}
    namespaces = sorted({case["namespace"] for case in evaluation["cases"]})
    for namespace in namespaces:
        cases = [case for case in evaluation["cases"] if case["namespace"] == namespace]
        answerable = [case for case in cases if case["target_ids"]]
        unanswerable = [case for case in cases if not case["target_ids"]]
        results[namespace] = {
            "case_count": len(cases),
            "answerable_case_count": len(answerable),
            "gold_id_count": sum(len(case["target_ids"]) for case in answerable),
            "unanswerable_case_count": len(unanswerable),
            "timing": {
                "known_case_count": sum(
                    any(observed[case["id"]].get(field) is not None for field in TIMING_FIELDS)
                    for case in cases
                ),
                "unknown_case_count": sum(
                    not any(observed[case["id"]].get(field) is not None for field in TIMING_FIELDS)
                    for case in cases
                ),
            },
            "lanes": {},
        }
        for lane in LANES:
            gold_hits = 0
            query_recalls = []
            reciprocal_ranks = []
            answerable_misses = 0
            unanswerable_candidate_cases = 0
            unanswerable_final_hit_cases = 0
            all_returned: set[str] = set()
            returned_count = 0
            for case in cases:
                row = observed[case["id"]]
                identities = lane_ids(row, lane)
                top_five = identities[:5]
                returned_count += len(identities)
                all_returned.update(identities)
                if case["target_ids"]:
                    targets = set(case["target_ids"])
                    query_gold_hits = len(targets.intersection(top_five))
                    gold_hits += query_gold_hits
                    query_recalls.append(query_gold_hits / len(targets))
                    first_rank = next(
                        (rank for rank, identity in enumerate(top_five, start=1) if identity in targets),
                        None,
                    )
                    if first_rank is None:
                        answerable_misses += 1
                        reciprocal_ranks.append(0.0)
                    else:
                        reciprocal_ranks.append(1.0 / first_rank)
                else:
                    if top_five:
                        unanswerable_candidate_cases += 1
                    if lane == "rrf" and identities:
                        unanswerable_final_hit_cases += 1
            canonical = canonical_by_namespace[namespace]
            canonical_returned = all_returned.intersection(canonical)
            noncanonical_returned = all_returned.difference(canonical)
            lane_result = {
                "macro_recall_at_5": round(sum(query_recalls) / len(query_recalls), 6)
                if query_recalls else None,
                "micro_gold_recall_at_5": round(gold_hits / results[namespace]["gold_id_count"], 6)
                if results[namespace]["gold_id_count"] else None,
                # Kept as an explicit compatibility alias for the original v1 report.
                "recall_at_5": round(gold_hits / results[namespace]["gold_id_count"], 6)
                if results[namespace]["gold_id_count"] else None,
                "gold_ids_retrieved_at_5": gold_hits,
                "answerable_miss_case_count_at_5": answerable_misses,
                "mrr_at_5": round(sum(reciprocal_ranks) / len(answerable), 6)
                if answerable else None,
                "unanswerable_candidate_top5_case_count": unanswerable_candidate_cases,
                "unanswerable_final_hit_case_count": (
                    unanswerable_final_hit_cases if lane == "rrf" else None
                ),
                "returned_id_count_all_ranks": returned_count,
                "unique_canonical_ids_all_ranks": len(canonical_returned),
                "noncanonical_id_count_all_ranks": len(noncanonical_returned),
            }
            results[namespace]["lanes"][lane] = lane_result

    return {
        "schema_version": "ceres-local-followup-retrieval-metrics-v2",
        "purpose": "Public development set diagnostics only; not independent quality acceptance.",
        "correction_note": (
            "Supersedes retrieval-dev-metrics-v1 by adding query-macro recall alongside "
            "the prior gold-ID-weighted micro recall; raw retrieval output is unchanged."
        ),
        "evaluation": {
            "path": str(eval_path),
            "sha256": sha256(eval_path),
            "version": evaluation["version"],
            "case_count": len(evaluation["cases"]),
        },
        "report": {"path": str(report_path), "sha256": sha256(report_path)},
        "index": {
            "path": str(index_path),
            "sha256": sha256(index_path),
            "embedding_revision": report["index_manifest"]["embedding_revision"],
            "dimensions": report["index_manifest"]["dimensions"],
        },
        "metrics_definition": {
            "macro_recall_at_5": "unweighted mean of each answerable query's target-ID recall in lane top 5; query misses score 0",
            "micro_gold_recall_at_5": "relevant target IDs found in lane top 5 divided by all target-ID occurrences in answerable cases; this equals the v1 recall_at_5",
            "mrr_at_5": "mean reciprocal rank of the first target ID per answerable query; misses score 0 and remain in the denominator",
            "unanswerable_candidate_top5_case_count": "no-answer queries with any raw lane candidate in top 5; raw BM25/dense candidates are not final relevance decisions",
            "unanswerable_final_hit_case_count": "no-answer queries with any final relevance-filtered RRF hit; this is the false-positive count",
            "canonical_ids": "returned IDs checked against the current same-namespace IDs in the verified local index",
            "timing": "the stored retrieval report has no elapsed/latency fields, so timing remains unknown",
        },
        "overall_public_dev_passed_cases": sum(bool(row["passed"]) for row in report["cases"]),
        "overall_public_dev_case_count": len(report["cases"]),
        "namespaces": results,
    }


def render_markdown(result: dict) -> str:
    lines = [
        "# Public retrieval development metrics (v2) - macro and micro recall",
        "",
        "This is a diagnostic summary of the 18-case public development set, not independent quality acceptance.",
        "",
        f"- Evaluation `{result['evaluation']['version']}` SHA-256: `{result['evaluation']['sha256']}`.",
        f"- Raw report SHA-256: `{result['report']['sha256']}`.",
        f"- Index SHA-256: `{result['index']['sha256']}`; BGE revision `{result['index']['embedding_revision']}`, {result['index']['dimensions']} dimensions.",
        f"- Existing retrieval smoke: {result['overall_public_dev_passed_cases']}/{result['overall_public_dev_case_count']} cases passed. This is the calibrated development set.",
        "",
        "This corrected v2 report adds query-macro Recall@5 to the prior gold-ID-weighted micro Recall@5. Ceres1-style macro recall is the unweighted mean of each answerable query's recall; a query with no target ID in top 5 scores zero. Micro recall weights each gold target ID equally. MRR@5 takes the first gold ID per answerable query, scores misses as zero, and keeps every answerable query in the denominator. BM25 and dense no-answer counts below describe raw candidate presence, not final false positives; the RRF column uses relevance-filtered final hits. The v1 report and raw output remain unchanged.",
        "",
        "## Query counts and timing",
        "",
        "| Namespace | Cases | Answerable | Gold IDs | No-answer | Timing unknown |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for namespace, data in result["namespaces"].items():
        lines.append(
            f"| {namespace} | {data['case_count']} | {data['answerable_case_count']} | {data['gold_id_count']} | {data['unanswerable_case_count']} | {data['timing']['unknown_case_count']} |"
        )
    lines += [
        "",
        "## Lane metrics",
        "",
        "| Namespace | Lane | Macro Recall@5 | Micro Gold Recall@5 | Gold IDs @5 | MRR@5 | Answerable misses | No-answer candidates in top 5 | No-answer final RRF hits | Unique canonical IDs | Noncanonical IDs |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for namespace, data in result["namespaces"].items():
        for lane, metrics in data["lanes"].items():
            final_hits = metrics["unanswerable_final_hit_case_count"]
            final_hits_text = "—" if final_hits is None else str(final_hits)
            lines.append(
                f"| {namespace} | {lane} | {metrics['macro_recall_at_5']} | {metrics['micro_gold_recall_at_5']} | {metrics['gold_ids_retrieved_at_5']} | {metrics['mrr_at_5']} | {metrics['answerable_miss_case_count_at_5']} | {metrics['unanswerable_candidate_top5_case_count']} | {final_hits_text} | {metrics['unique_canonical_ids_all_ranks']} | {metrics['noncanonical_id_count_all_ranks']} |"
            )
    lines += [
        "",
        "All returned IDs in the captured lanes mapped to canonical IDs in the matching namespace of this verified index. The report has no search duration fields, so all 18 query timings remain unknown.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval", type=Path, default=Path("evals/ceres2-optimization-retrieval-dev.json"))
    parser.add_argument("--report", type=Path, default=Path("work/local-followup/tmp/real-bge-public-dev-report.json"))
    parser.add_argument("--index", type=Path, default=Path("data/indexes/hybrid.sqlite3"))
    parser.add_argument("--output", type=Path, default=Path("work/local-followup/03/retrieval-dev-metrics-v2.json"))
    parser.add_argument("--markdown", type=Path, default=Path("work/local-followup/03/retrieval-dev-metrics-v2.md"))
    args = parser.parse_args()
    result = score(args.eval, args.report, args.index)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "schema_version": result["schema_version"],
        "overall_public_dev_passed_cases": result["overall_public_dev_passed_cases"],
        "overall_public_dev_case_count": result["overall_public_dev_case_count"],
        "namespace_counts": {key: value["case_count"] for key, value in result["namespaces"].items()},
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
