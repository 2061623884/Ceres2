"""Run the requested hybrid retrieval queries and retain lane/rank evidence."""

from __future__ import annotations

import json
import math
import sqlite3
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.knowledge import cli  # noqa: E402


INDEX = ROOT / "data" / "indexes" / "hybrid.sqlite3"
CASES = (
    ("recipe", "番茄炒蛋", ["dish-fanqie-chao-dan"]),
    ("recipe", "什锦炒饭", ["dish-yangzhou-chao-fan"]),
    ("product", "炒饭用的虾仁", ["demo:shrimp-200g"]),
    ("product", "苹果", []),
    ("policy", "未发货取消订单", ["P-REF-01"]),
    ("policy", "生鲜坏了能退吗", ["P-QUA-01"]),
    ("policy", "火星定制商品特殊条款", []),
    ("policy", "怎么修自行车", []),
    ("recipe", "蛋", [
        "dish-fanqie-chao-dan",
        "dish-dan-chao-fan",
        "dish-yangzhou-chao-fan",
        "dish-jiajiao-chaodan",
    ]),
)


def run_query(namespace: str, query: str) -> dict:
    old_argv = sys.argv
    output = StringIO()
    try:
        sys.argv = [
            "app.knowledge.cli",
            "hybrid",
            "--namespace",
            namespace,
            "--query",
            query,
            "--index",
            str(INDEX),
        ]
        with redirect_stdout(output):
            cli.main()
    finally:
        sys.argv = old_argv
    return json.loads(output.getvalue())


def verify_index() -> dict:
    with sqlite3.connect(f"file:{INDEX}?mode=ro", uri=True) as db:
        manifest = json.loads(db.execute("SELECT content FROM manifest").fetchone()[0])
        counts = {
            namespace: db.execute(
                "SELECT COUNT(*) FROM documents WHERE namespace = ?", (namespace,)
            ).fetchone()[0]
            for namespace in ("recipe", "product", "policy")
        }
        rows = db.execute("SELECT namespace, document, embedding FROM documents").fetchall()
    assert counts == {"recipe": 8, "product": 71, "policy": 11}, counts
    assert "offers.json" not in manifest["files"]
    assert all(len(embedding) == 512 * 4 for _, _, embedding in rows)
    docs = [json.loads(document) for _, document, _ in rows]
    forbidden = {"price", "price_fen", "available_qty", "stock", "inventory"}
    assert all(not forbidden.intersection(doc) for doc in docs)
    product_docs = [doc for doc in docs if doc["namespace"] == "product"]
    assert all("price_fen" not in doc["text"] and "available_qty" not in doc["text"] for doc in product_docs)
    return {
        "counts": counts,
        "documents": len(docs),
        "all_vectors_512_f32": True,
        "offers_fixture_excluded": True,
        "dynamic_price_inventory_fields_absent": True,
        "manifest": manifest,
    }


def main() -> None:
    index_audit = verify_index()
    cases = []
    positive_failures = []
    for namespace, query, positives in CASES:
        result = run_query(namespace, query)
        sparse = result["sparse"]
        dense = result["dense"]
        candidates = result["candidates"]
        hits = result["hits"]
        assert dense, (namespace, query, "empty dense lane")
        assert all(math.isfinite(score) for _, score in dense)
        for hit in candidates:
            expected_score = sum(1 / (60 + rank) for rank in hit["ranks"].values())
            assert math.isclose(hit["rrf_score"], expected_score, rel_tol=0, abs_tol=1e-15)
        hit_ids = {hit["id"] for hit in hits}
        candidate_ids = {candidate["id"] for candidate in candidates}
        rrf_recall = [item for item in positives if item in candidate_ids]
        hit_recall = [item for item in positives if item in hit_ids]
        if namespace == "recipe" and query == "蛋":
            if set(positives) - hit_ids:
                positive_failures.append({
                    "namespace": namespace,
                    "query": query,
                    "missing_ids_in_rrf_candidates": sorted(set(positives) - candidate_ids),
                    "missing_ids_in_hits": sorted(set(positives) - hit_ids),
                    "hit_ids": sorted(hit_ids),
                })
        cases.append({
            "namespace": namespace,
            "query": query,
            "expected_positive_ids": positives,
            "positive_ids_recalled_in_rrf_candidates": rrf_recall,
            "positive_ids_recalled_in_relevance_hits": hit_recall,
            "hits_empty": not hits,
            "sparse_count": len(sparse),
            "sparse_top5": [{"id": item, "score": score} for item, score in sparse[:5]],
            "dense_count": len(dense),
            "dense_top3": [{"id": item, "score": score} for item, score in dense[:3]],
            "rrf_top5": [
                {"id": hit["id"], "score": hit["rrf_score"], "ranks": hit["ranks"], "scores": hit["scores"]}
                for hit in candidates[:5]
            ],
            "relevance_hits_top5": [
                {"id": hit["id"], "score": hit["rrf_score"], "ranks": hit["ranks"], "scores": hit["scores"]}
                for hit in hits[:5]
            ],
            "rrf_formula_verified": True,
        })
    report = {
        "index_path": str(INDEX),
        "model_id": index_audit["manifest"].get("embedding_model"),
        "model_revision": index_audit["manifest"].get("embedding_revision"),
        "dimensions": index_audit["manifest"].get("dimensions"),
        "index_audit": index_audit,
        "queries": cases,
        "positive_recall_validation": {
            "single_character_egg_query_expected_ids": [
                item for namespace, query, positives in CASES
                if namespace == "recipe" and query == "蛋" for item in positives
            ],
            "failures": positive_failures,
            "all_expected_ids_in_rrf_candidates": not any(row["missing_ids_in_rrf_candidates"] for row in positive_failures),
            "all_expected_ids_in_relevance_hits": not positive_failures,
        },
    }
    output_path = Path(__file__).with_name("hybrid-query-smoke-v4-literal-or-dense-2026-10-07.json")
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False))
    assert not positive_failures, positive_failures


if __name__ == "__main__":
    main()
