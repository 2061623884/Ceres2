"""Sample the current global canonical-scope overview against the existing v3 index."""

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
FIXTURES = ROOT / "data/fixtures"
OUTPUT = Path(__file__).with_name("graph-global-overview-v3-smoke-2026-10-07.json")
QUERY = "这批家常菜共有哪几类食材，哪些菜用鸡蛋"


def quantity_text(item: dict) -> str:
    for unit in ("g", "ml", "pc"):
        key = f"quantity_{unit}"
        if key in item:
            amount = item[key]
            return f"{int(amount) if int(amount) == amount else amount}{unit}"
    return ""


def audit(result: dict) -> dict:
    recipe_data = json.loads((FIXTURES / "recipes.json").read_text())
    ingredient_data = json.loads((FIXTURES / "ingredients.json").read_text())
    dishes = recipe_data["dishes"]
    ingredients = ingredient_data["ingredients"]
    egg_dishes = {
        dish["dish_id"]: next(item for item in dish["required_items"] if item["ingredient_id"] == "egg")
        for dish in dishes if any(item["ingredient_id"] == "egg" for item in dish["required_items"])
    }

    context_reports = result["context"].get("reports", [])
    report_table = pd.read_parquet(GRAPH_ROOT / "output/community_reports.parquet")
    communities = pd.read_parquet(GRAPH_ROOT / "output/communities.parquet")
    entities = pd.read_parquet(GRAPH_ROOT / "output/entities.parquet")
    report_scope: set[str] = set()
    mapped_report_ids = []
    for report in context_reports:
        report_id = str(report["id"])
        matches = report_table[report_table["human_readable_id"].astype(str) == report_id]
        if len(matches) != 1:
            continue
        mapped_report_ids.append(report_id)
        community_id = matches.iloc[0]["community"]
        community_rows = communities[communities["community"] == community_id]
        if len(community_rows) == 1:
            report_scope.update(community_rows.iloc[0]["entity_ids"])

    fact_ids = {row["id"] for row in result["canonical_facts"]}
    fact_by_id = {row["id"]: row for row in result["canonical_facts"]}
    scope_audit = {
        "retrieved_report_count": len(context_reports),
        "mapped_retrieved_report_count": len(mapped_report_ids),
        "retrieved_community_entity_count": len(report_scope),
        "canonical_fact_count": len(fact_ids),
        "all_canonical_facts_in_retrieved_community_scope": fact_ids <= report_scope,
        "entity_numbers_in_scope": set(result["selection"]["entity_numbers"]) <= set(
            entities.loc[entities["id"].isin(report_scope), "human_readable_id"].astype(int)
        ),
    }

    egg_map = result["ingredient_recipes"].get("ingredient:egg", {"ingredient": None, "recipes": []})
    egg_rows = []
    observed_egg_ids = set()
    for row in egg_map["recipes"]:
        recipe_id = row["recipe_id"].removeprefix("recipe:")
        observed_egg_ids.add(recipe_id)
        source = egg_dishes.get(recipe_id)
        egg_rows.append({
            "dish_id": recipe_id,
            "recipe_title": row["title"],
            "expected_baseline_quantity": quantity_text(source) if source else None,
            "relationship_has_baseline_quantity": bool(source and quantity_text(source) in row["source_description"]),
            "relationship_id": row["relationship_id"],
            "relationship_source": row["source_description"],
        })
    expected_egg_ids = set(egg_dishes)

    kind_rows = []
    for ingredient in ingredients:
        fact = fact_by_id.get("ingredient:" + ingredient["ingredient_id"])
        kind_rows.append({
            "ingredient_id": ingredient["ingredient_id"],
            "expected_kind": ingredient["kind"],
            "canonical_fact_present": fact is not None,
            "kind_present": bool(fact and f"类别 {ingredient['kind']}；来源 ingredients.json/{ingredient['ingredient_id']}" in fact["description"]),
            "source_description": fact["description"] if fact else None,
        })

    entity_by_number = entities.set_index("human_readable_id")["id"].to_dict()
    selector_recipe_ids = {
        entity_by_number[number].removeprefix("recipe:")
        for number in result["selection"]["entity_numbers"]
        if number in entity_by_number and entity_by_number[number].startswith("recipe:")
    }
    selected_egg_recipes = sorted(selector_recipe_ids & expected_egg_ids)
    return {
        "query": QUERY,
        "query_revision": result["query_revision"],
        "selection": result["selection"],
        "model_selected_egg_recipe_ids": selected_egg_recipes,
        "selection_recall_for_four_egg_recipes": f"{len(selected_egg_recipes)}/{len(expected_egg_ids)}",
        "selection_recall_interpretation": "This records the model's original selection; the host overview retains canonical facts from retrieved communities and does not claim the selector improved.",
        "scope": scope_audit,
        "egg_ingredient_map": {
            "ingredient_title": egg_map["ingredient"],
            "expected_recipe_count": len(expected_egg_ids),
            "observed_recipe_count": len(observed_egg_ids),
            "all_expected_recipes_present": expected_egg_ids <= observed_egg_ids,
            "all_baseline_quantities_present": len(egg_rows) >= len(expected_egg_ids) and all(row["relationship_has_baseline_quantity"] for row in egg_rows if row["dish_id"] in expected_egg_ids),
            "recipes": sorted(egg_rows, key=lambda row: row["dish_id"]),
        },
        "ingredient_kind_sources": kind_rows,
        "all_fixture_ingredient_kinds_and_sources_present": all(row["canonical_fact_present"] and row["kind_present"] for row in kind_rows),
        "answer": result["answer"],
        "provider_usage": {
            "completion_calls": [call.get("usage") for call in result["calls"] if call.get("kind") == "completion"],
            "embedding_calls": [call for call in result["calls"] if call.get("kind") == "embedding"],
        },
        "canonical_fact_ids": sorted(fact_ids),
        "ingredient_relationship_count": sum(len(entry["recipes"]) for entry in result["ingredient_recipes"].values()),
        "tool_payload_allowlist": ["method", "canonical_facts", "ingredient_recipes", "graph_revision", "query_revision"],
        "interpretation": "One real-provider query against the existing v3 GraphRAG index. Canonical overview facts remain limited to entities in communities actually returned by this query.",
    }


async def query_global() -> dict:
    from app.knowledge.graph import search
    return await search(GRAPH_ROOT, QUERY, "global")


def main() -> None:
    values = dotenv_values(ENV_PATH, encoding="utf-8")
    selected = {
        "OPENAI_BASE_URL": values.get("OPENAI_BASE_URL"),
        "OPENAI_API_KEY": values.get("OPENAI_API_KEY"),
        "LLM_MODEL": values.get("LLM_MODEL"),
    }
    if not all(isinstance(value, str) and value.strip() for value in selected.values()):
        raise RuntimeError("approved provider config is incomplete")
    os.environ.update(selected)
    from app.core.config import get_settings
    get_settings.cache_clear()
    graph_result = asyncio.run(query_global())
    report = audit(graph_result)
    report["source_graph_result"] = {
        "method": graph_result["method"],
        "canonical_facts": graph_result["canonical_facts"],
        "ingredient_recipes": graph_result["ingredient_recipes"],
        "query_revision": graph_result["query_revision"],
        "manifest": graph_result["manifest"],
        "calls": graph_result["calls"],
    }
    report["provider_model"] = selected["LLM_MODEL"]
    report["provider_host"] = urlparse(selected["OPENAI_BASE_URL"]).hostname
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    summary = {key: report[key] for key in (
        "query_revision", "selection", "model_selected_egg_recipe_ids",
        "selection_recall_for_four_egg_recipes", "scope", "egg_ingredient_map",
        "all_fixture_ingredient_kinds_and_sources_present", "provider_model", "provider_host",
    )}
    summary["output_path"] = str(OUTPUT)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
