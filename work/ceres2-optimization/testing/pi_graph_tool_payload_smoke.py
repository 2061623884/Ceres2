"""Pass the sampled real Global result through the Pi host tool projection."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

SAMPLE = Path(__file__).with_name("graph-global-overview-v3-smoke-2026-10-07.json")
OUTPUT = Path(__file__).with_name("pi-graph-tool-payload-smoke-2026-10-07.json")
QUERY = "这批家常菜共有哪几类食材，哪些菜用鸡蛋"


def nested_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from nested_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_keys(child)


def main() -> None:
    sample = json.loads(SAMPLE.read_text())
    source = sample["source_graph_result"]
    from sqlalchemy.orm import sessionmaker
    from app.core.database import create_db_engine, init_db
    from app.services.catalog_service import CatalogService
    from app.services.knowledge_service import knowledge
    from app.services.pi_product_runtime import PiProductRuntime
    from app.services.seed_service import seed_catalog

    folder = Path(__file__).with_name("tmp")
    folder.mkdir(parents=True, exist_ok=True)
    database = folder / f"pi-graph-tool-payload-{os.getpid()}.sqlite3"
    for suffix in ("", "-wal", "-shm"):
        Path(str(database) + suffix).unlink(missing_ok=True)
    engine = create_db_engine(f"sqlite:///{database}")
    init_db(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    with sessions.begin() as db:
        seed_catalog(db, ROOT / "data/fixtures")

    noop = lambda *_args, **_kwargs: {}
    original_graph = knowledge.graph
    knowledge.graph = lambda query, method="local": source
    try:
        with sessions() as db:
            runtime = PiProductRuntime(
                catalog=CatalogService(db), assert_current=lambda: None, run_id="graph-tool-smoke",
                route_request=noop, context={}, memory_command=noop, product_search=noop,
                comparison_search=noop, candidate_resolve=noop, history_command=noop,
                explore_products=noop, select_question_products=noop, activity_active=lambda: False,
                publish_interim=lambda *_args: None,
            )
            result = runtime._tool("search_recipe_relations", {"query": QUERY})
    finally:
        knowledge.graph = original_graph
        knowledge.close()
        engine.dispose()

    evidence = result["graph_evidence"]
    expected_evidence_keys = {"method", "canonical_facts", "ingredient_recipes", "graph_revision", "query_revision"}
    forbidden = {"answer", "context", "reports", "community_reports", "summary", "full_content"}
    all_keys = set(nested_keys(result))
    forbidden_present = sorted(forbidden & all_keys)
    report = {
        "query": QUERY,
        "tool_result_keys": sorted(result),
        "graph_evidence_keys": sorted(evidence),
        "graph_evidence_keys_match_contract": set(evidence) == expected_evidence_keys,
        "graph_method": evidence["method"],
        "query_revision": evidence["query_revision"],
        "canonical_fact_count": len(evidence["canonical_facts"]),
        "ingredient_relation_count": sum(len(entry["recipes"]) for entry in evidence["ingredient_recipes"].values()),
        "egg_relation_count": len(evidence["ingredient_recipes"].get("ingredient:egg", {}).get("recipes", [])),
        "returned_dish_count": len(result["dishes"]),
        "forbidden_summary_or_report_keys_present": forbidden_present,
        "free_community_summary_not_forwarded": not forbidden_present,
        "source_sample_retrieved_report_count": sample["scope"]["retrieved_report_count"],
        "source_sample_had_retrieved_report_context": sample["scope"]["retrieved_report_count"] > 0,
        "interpretation": "Uses the actual sampled GraphRAG Global canonical facts and relationship map, then inspects the host Pi tool projection. The Pi result omits the generated GraphRAG answer and community report context.",
    }
    assert report["graph_evidence_keys_match_contract"]
    assert report["free_community_summary_not_forwarded"]
    assert evidence["canonical_facts"] == source["canonical_facts"]
    assert evidence["ingredient_recipes"] == source["ingredient_recipes"]
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
