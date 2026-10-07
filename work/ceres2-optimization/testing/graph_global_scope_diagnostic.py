"""Capture GraphRAG's selected IDs and exact retrieved scope, never prose."""

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
OUTPUT = Path(__file__).with_name("graph-query-v3-global-scope-diagnostic-2026-10-07.json")
QUERY = "这批家常菜共有哪几类食材，哪些菜用鸡蛋"


async def main_async() -> dict:
    from graphrag import api
    from graphrag.prompts.query.global_search_reduce_system_prompt import NO_DATA_ANSWER
    from app.knowledge import graph
    from app.knowledge.providers import CALLS

    capture: dict = {}
    original_global_search = api.global_search

    async def capture_global_search(**kwargs):
        answer, context = await original_global_search(**kwargs)
        capture["answer_is_no_data"] = answer == NO_DATA_ANSWER
        if answer != NO_DATA_ANSWER:
            try:
                parsed = json.loads(answer)
                ids = parsed.get("entity_ids") if isinstance(parsed, dict) else None
                capture["selection_shape_valid"] = isinstance(ids, list) and all(isinstance(item, str) for item in ids)
                capture["selected_entity_ids"] = ids if capture["selection_shape_valid"] else []
            except (json.JSONDecodeError, AttributeError):
                capture["selection_shape_valid"] = False
                capture["selected_entity_ids"] = []
        else:
            capture["selection_shape_valid"] = True
            capture["selected_entity_ids"] = []
        capture["context"] = context
        capture["call_count"] = len(CALLS) - capture["calls_before"]
        return answer, context

    capture["calls_before"] = len(CALLS)
    api.global_search = capture_global_search
    failure = None
    result = None
    try:
        result = await graph.search(GRAPH_ROOT, QUERY, "global")
    except Exception as exc:
        safe_message = str(exc) if str(exc) == "GraphRAG selected a reference outside the retrieved context" else None
        failure = {"type": type(exc).__name__, "message": safe_message}
    finally:
        api.global_search = original_global_search

    context = capture.get("context")
    projected = {}
    if context is not None:
        projected = {
            key: json.loads(value.to_json(orient="records", force_ascii=False)) if isinstance(value, pd.DataFrame) else value
            for key, value in context.items()
        }
    output = GRAPH_ROOT / "output"
    entities = pd.read_parquet(output / "entities.parquet")
    communities = pd.read_parquet(output / "communities.parquet")
    reports = pd.read_parquet(output / "community_reports.parquet")
    titles = {row["entity"] for row in projected.get("entities", [])}
    for relation in projected.get("relationships", []):
        titles.update((relation["source"], relation["target"]))
    entity_context_ids = set(entities.loc[entities["title"].isin(titles), "id"])
    scope = set(entity_context_ids)
    context_report_ids = {str(row["id"]) for row in projected.get("reports", [])}
    communities_by_id = communities.set_index("community")
    report_mappings = []
    for _, report in reports.iterrows():
        if str(report["human_readable_id"]) in context_report_ids:
            community = communities_by_id.loc[report["community"]]
            member_ids = [str(identity) for identity in community["entity_ids"]]
            scope.update(community["entity_ids"])
            report_mappings.append({
                "context_report_id": str(report["human_readable_id"]),
                "report_human_readable_id": int(report["human_readable_id"]),
                "community_id": int(report["community"]),
                "member_count": len(member_ids),
                "member_ids": member_ids,
            })
    selected_ids = capture.get("selected_entity_ids", [])
    selected_rows = entities.set_index("id")
    selected_details = []
    for identity in selected_ids:
        detail = {"id": identity, "in_exact_scope_set": identity in scope}
        if identity in selected_rows.index:
            row = selected_rows.loc[identity]
            detail.update({"type": str(row["type"]), "title": str(row["title"]), "human_readable_id": int(row["human_readable_id"])})
        selected_details.append(detail)

    return {
        "provider_model": graph.get_settings().llm_model,
        "provider_host": urlparse(graph.get_settings().openai_base_url).hostname,
        "query": QUERY,
        "failure": failure,
        "search_returned": result is not None,
        "answer_is_no_data": capture.get("answer_is_no_data"),
        "selection_shape_valid": capture.get("selection_shape_valid"),
        "selected_entity_ids": selected_ids,
        "selected_entity_details": selected_details,
        "context_keys": {key: len(value) if isinstance(value, list) else None for key, value in projected.items()},
        "entity_context_ids": sorted(str(identity) for identity in entity_context_ids),
        "context_report_ids": sorted(context_report_ids),
        "report_id_mappings": report_mappings,
        "scope_entity_count": len(scope),
        "out_of_scope_entity_ids": sorted(identity for identity in selected_ids if identity not in scope),
        "call_count": capture.get("call_count"),
    }


def main() -> None:
    values = dotenv_values(ENV_PATH, encoding="utf-8")
    selected = {key: values.get(key) for key in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "LLM_MODEL")}
    if not all(isinstance(value, str) and value.strip() for value in selected.values()):
        raise RuntimeError("approved provider config is incomplete")
    for key, value in selected.items():
        os.environ[key] = value
    from app.core.config import get_settings

    get_settings.cache_clear()
    report = asyncio.run(main_async())
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
