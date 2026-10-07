"""Compare the v3 GraphRAG sample with canonical recipe/ingredient facts."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QUERY_REPORT = Path(__file__).with_name("graph-query-smoke-v3-canonical-2026-10-07.json")
FIXTURES = ROOT / "data/fixtures"
OUTPUT = Path(__file__).with_name("graph-query-v3-canonical-content-audit-2026-10-07.json")


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def main() -> None:
    queries = json.loads(QUERY_REPORT.read_text())["queries"]
    local = next(row for row in queries if row["query"].startswith("番茄炒蛋"))
    global_row = next(row for row in queries if row["method"] == "global")
    local_answer = compact(local["answer"])
    global_answer = compact(global_row.get("answer", ""))
    unknown = next(row for row in queries if "独角鲸" in row["query"])
    recipe_data = json.loads((FIXTURES / "recipes.json").read_text())
    ingredients_data = json.loads((FIXTURES / "ingredients.json").read_text())
    egg_recipes = []
    for dish in recipe_data["dishes"]:
        item = next((row for row in dish["required_items"] if row["ingredient_id"] == "egg"), None)
        if item:
            amount = item.get("quantity_pc")
            assert amount is not None, dish["dish_id"]
            egg_recipes.append({
                "dish_id": dish["dish_id"],
                "name": dish["name"],
                "egg_quantity_pc": amount,
                "name_found_in_global": dish["name"] in global_answer,
                "quantity_found_in_global": f"鸡蛋{amount:g}pc" in global_answer,
            })
    kinds = sorted({row["kind"] for row in ingredients_data["ingredients"]})
    pork = next(row for row in ingredients_data["ingredients"] if row["ingredient_id"] == "pork")
    global_plain = global_row.get("answer", "")
    found_kinds = [kind for kind in kinds if re.search(rf"(?<![A-Za-z]){re.escape(kind)}(?![A-Za-z])", global_plain)]
    pork_unknown_phrases = [
        line.strip()
        for line in global_row.get("answer", "").splitlines()
        if "猪肉" in line and ("类别保持未知" in line or "kind" in line.lower() and "未知" in line)
    ]
    report = {
        "source_recipe_version": recipe_data["version"],
        "source_ingredient_version": ingredients_data["version"],
        "local_query": {
            "tomato_300g_found": "番茄300g" in local_answer,
            "egg_3pc_found": "鸡蛋3pc" in local_answer,
        },
        "global_query": {
            "expected_egg_recipe_count": len(egg_recipes),
            "egg_recipes": egg_recipes,
            "all_egg_recipe_names_found": all(row["name_found_in_global"] for row in egg_recipes),
            "all_egg_quantities_found": all(row["quantity_found_in_global"] for row in egg_recipes),
            "expected_ingredient_kinds": kinds,
            "ingredient_kinds_found": found_kinds,
            "kind_list_complete": kinds == found_kinds,
            "pork_source_kind": pork["kind"],
            "pork_kind_marked_unknown_in_answer": bool(pork_unknown_phrases),
            "pork_unknown_phrases": pork_unknown_phrases,
        },
        "unknown_recipe": {
            "query": unknown["query"],
            "selected_entity_numbers": unknown.get("selection", {}).get("entity_numbers", []),
            "selected_entity_ids": [row.get("id") for row in unknown.get("canonical_facts", [])],
            "canonical_fact_count": len(unknown.get("canonical_facts", [])),
            "empty_selection": not unknown.get("selection", {}).get("entity_numbers", []),
        },
        "interpretation": "One online GraphRAG sample only; these checks compare that response with canonical demo fixtures and do not establish general answer reliability.",
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
