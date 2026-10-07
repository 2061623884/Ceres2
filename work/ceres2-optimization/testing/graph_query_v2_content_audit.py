"""Compare the sampled GraphRAG answers with canonical recipe/ingredient facts."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QUERY_REPORT = Path(__file__).with_name("graph-query-smoke-v3-2026-10-07.json")
FIXTURES = ROOT / "data/fixtures"
OUTPUT = Path(__file__).with_name("graph-query-v3-content-audit-2026-10-07.json")


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def main() -> None:
    queries = json.loads(QUERY_REPORT.read_text())["queries"]
    by_method = {row["method"]: row for row in queries}
    local_answer = compact(by_method["local"]["answer"])
    global_answer = compact(by_method["global"]["answer"])
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
            "ingredient_kinds_found": [kind for kind in kinds if f"`{kind}`" in by_method["global"]["answer"]],
            "pork_source_kind": pork["kind"],
            "unsupported_claim_pork_kind_unknown": "猪肉自身的kind仍属未知" in global_answer,
        },
        "interpretation": "One online GraphRAG sample only; these checks compare that response with canonical demo fixtures and do not establish general answer reliability.",
    }
    report["global_query"]["kind_list_complete"] = report["global_query"]["expected_ingredient_kinds"] == report["global_query"]["ingredient_kinds_found"]
    report["global_query"]["pork_kind_claim_conflicts_with_source"] = report["global_query"]["unsupported_claim_pork_kind_unknown"] and pork["kind"] == "meat"
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
