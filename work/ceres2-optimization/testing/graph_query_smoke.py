"""Run the requested local and global GraphRAG queries with the approved provider."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

ENV_PATH = Path("/home/amax/Documents/projects/Agent/Agent产品/Ceres2/.env")
GRAPH_ROOT = ROOT / "data/indexes/graphrag"
OUTPUT = Path(__file__).with_name("graph-query-smoke-v3-canonical-2026-10-07.json")
QUERIES = (
    ("local", "番茄炒蛋需要哪些食材与商品"),
    ("global", "这批家常菜共有哪几类食材，哪些菜用鸡蛋"),
    ("local", "请查询独角鲸奶泡松露汤的菜谱、必需食材和用量"),
)


def summarize_calls(calls: list[dict]) -> dict:
    completions = [call for call in calls if call.get("kind") == "completion"]
    embeddings = [call for call in calls if call.get("kind") == "embedding"]
    return {
        "call_count": len(calls),
        "completion_count": len(completions),
        "embedding_count": len(embeddings),
        "completion_usage": [call.get("usage") for call in completions],
        "embedding_usage": [
            {"prompt_tokens": call.get("prompt_tokens"), "texts": call.get("texts")}
            for call in embeddings
        ],
    }


def audit_source_map(result: dict) -> dict:
    output = GRAPH_ROOT / "output"
    source_map = result["source_map"]
    source_tables = {
        "entities": pd.read_parquet(output / "entities.parquet"),
        "relationships": pd.read_parquet(output / "relationships.parquet"),
    }
    audit = {}
    for name, frame in source_tables.items():
        rows = source_map[name]
        expected = set(frame["id"].astype(str))
        mapped = {str(row["id"]) for row in rows}
        human_ids = [int(row["human_readable_id"]) for row in rows]
        audit[name] = {
            "expected_ids": len(expected),
            "mapped_ids": len(mapped),
            "ids_match": mapped == expected,
            "human_readable_ids_unique": len(human_ids) == len(set(human_ids)),
        }
        assert audit[name]["ids_match"], name
        assert audit[name]["human_readable_ids_unique"], name
    return audit


async def run_queries() -> list[dict]:
    from app.knowledge.graph import search

    results = []
    for method, query in QUERIES:
        try:
            result = await search(GRAPH_ROOT, query, method)
        except Exception as exc:
            safe_message = str(exc) if str(exc) == "GraphRAG selected a reference outside the retrieved context" else None
            results.append({"method": method, "query": query,
                "failure": {"type": type(exc).__name__, "message": safe_message}})
            continue
        assert result["answer"].strip(), (method, "empty answer")
        source_map_audit = audit_source_map(result)
        results.append({
            "method": method,
            "query": query,
            "answer": result["answer"],
            "selection": result["selection"],
            "canonical_facts": result["canonical_facts"],
            "query_revision": result["query_revision"],
            "context": result["context"],
            "context_keys": {
                key: len(value) if isinstance(value, list) else None
                for key, value in result["context"].items()
            },
            "source_map_audit": source_map_audit,
            "call_usage": summarize_calls(result["calls"]),
            "source_map": result["source_map"],
        })
    return results


def main() -> None:
    values = dotenv_values(ENV_PATH, encoding="utf-8")
    selected = {
        "OPENAI_BASE_URL": values.get("OPENAI_BASE_URL"),
        "OPENAI_API_KEY": values.get("OPENAI_API_KEY"),
        "LLM_MODEL": values.get("LLM_MODEL"),
    }
    if not all(isinstance(value, str) and value.strip() for value in selected.values()):
        raise RuntimeError("approved provider config is incomplete")
    for name, value in selected.items():
        os.environ[name] = value

    from app.core.config import get_settings  # noqa: E402

    get_settings.cache_clear()
    try:
        results = asyncio.run(run_queries())
    except Exception as exc:
        response = getattr(exc, "response", None)
        failure = {
            "type": type(exc).__name__,
            "status_code": getattr(response, "status_code", None) or getattr(exc, "status_code", None),
            "code": getattr(exc, "code", None),
            "error_type": getattr(exc, "type", None),
        }
        OUTPUT.write_text(json.dumps({
            "provider_model": selected["LLM_MODEL"],
            "provider_host": urlparse(selected["OPENAI_BASE_URL"]).hostname,
            "failure": failure,
        }, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(failure, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    report = {
        "provider_model": selected["LLM_MODEL"],
        "provider_host": urlparse(selected["OPENAI_BASE_URL"]).hostname,
        "all_queries_succeeded": all("failure" not in row for row in results),
        "queries": results,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "provider_model": report["provider_model"],
        "provider_host": report["provider_host"],
        "queries": [
            {
                "method": row["method"],
                "query": row["query"],
                "answer": row.get("answer"),
                "selection": row.get("selection"),
                "canonical_fact_count": len(row.get("canonical_facts", [])),
                "context_keys": row.get("context_keys"),
                "source_map_audit": row.get("source_map_audit"),
                "call_usage": row.get("call_usage"),
                "failure": row.get("failure"),
            }
            for row in results
        ],
        "output_path": str(OUTPUT),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
