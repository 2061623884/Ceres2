"""Offline GraphRAG parquet/schema/config smoke with synthetic credentials."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.knowledge.graph import config, export_graph  # noqa: E402

FIXTURES = ROOT / "data/fixtures"
OUTPUT_ROOT = Path(__file__).with_name("tmp") / "graph-schema-smoke-2026-10-07"


def main() -> None:
    # This gate is offline. Synthetic values make the Pydantic config model
    # complete without reading the user's .env or invoking a provider.
    os.environ["OPENAI_BASE_URL"] = "https://schema-smoke.invalid/v1"
    os.environ["OPENAI_API_KEY"] = "schema-smoke-placeholder"
    os.environ["LLM_MODEL"] = "schema-smoke-model"

    manifest = export_graph(FIXTURES, OUTPUT_ROOT)
    graph_config = config(OUTPUT_ROOT)

    import pandas as pd

    expected_tables = {
        "entities": (OUTPUT_ROOT / "output/entities.parquet", {"id", "human_readable_id", "title", "type", "text_unit_ids"}),
        "relationships": (OUTPUT_ROOT / "output/relationships.parquet", {"id", "human_readable_id", "source", "target", "text_unit_ids"}),
        "text_units": (OUTPUT_ROOT / "output/text_units.parquet", {"id", "document_id", "entity_ids", "relationship_ids"}),
        "documents": (OUTPUT_ROOT / "output/documents.parquet", {"id", "namespace", "title", "text"}),
    }
    tables = {}
    for name, (path, required_columns) in expected_tables.items():
        frame = pd.read_parquet(path)
        assert len(frame) > 0, name
        assert required_columns <= set(frame.columns), (name, sorted(required_columns - set(frame.columns)))
        tables[name] = {"rows": len(frame), "columns": list(frame.columns)}

    assert manifest["counts"] == {"product": 71, "recipe": 8, "policy": 11}, manifest["counts"]
    graph_counts = manifest["graph_counts"]
    assert graph_counts["entities"] == tables["entities"]["rows"]
    assert graph_counts["relationships"] == tables["relationships"]["rows"]
    assert graph_counts["text_units"] == tables["text_units"]["rows"]
    assert graph_config.workflows == ["create_communities", "create_community_reports", "generate_text_embeddings"]
    assert graph_config.cache.type == "memory"
    assert graph_config.vector_store.type == "lancedb"
    assert graph_config.vector_store.vector_size == 512
    assert graph_config.completion_models["chat"].type == "ceres_json_mode"
    assert graph_config.embedding_models["bge"].type == "ceres_bge"
    assert graph_config.completion_models["chat"].model == "schema-smoke-model"

    summary = {
        "offline_only": True,
        "synthetic_provider_values": True,
        "provider_called": False,
        "source_counts": manifest["counts"],
        "graph_counts": graph_counts,
        "tables": tables,
        "config": {
            "workflows": graph_config.workflows,
            "cache_type": graph_config.cache.type,
            "vector_store_type": graph_config.vector_store.type,
            "vector_size": graph_config.vector_store.vector_size,
            "completion_type": graph_config.completion_models["chat"].type,
            "embedding_type": graph_config.embedding_models["bge"].type,
            "model_id": graph_config.completion_models["chat"].model,
        },
        "source_map_ids_unique": all(
            frame["id"].is_unique for frame in (pd.read_parquet(expected_tables[name][0]) for name in ("entities", "relationships", "text_units", "documents"))
        ),
        "output_root": str(OUTPUT_ROOT),
    }
    assert summary["source_map_ids_unique"]
    report = Path(__file__).with_name("graph-schema-smoke-2026-10-07.json")
    report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
