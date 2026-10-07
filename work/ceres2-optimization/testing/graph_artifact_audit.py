"""Audit complete GraphRAG tables, community coverage, and Lance dimensions."""

from __future__ import annotations

import json
from pathlib import Path

import lancedb
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
GRAPH_ROOT = ROOT / "data/indexes/graphrag"
OUTPUT = Path(__file__).with_name("graph-artifact-audit-v3-2026-10-07.json")


def values(series) -> set[str]:
    return {str(value) for row in series for value in row}


def main() -> None:
    output_dir = GRAPH_ROOT / "output"
    names = ("entities", "relationships", "text_units", "documents", "communities", "community_reports")
    frames = {name: pd.read_parquet(output_dir / f"{name}.parquet") for name in names}
    assert all(len(frame) for frame in frames.values())

    entity_ids = set(frames["entities"]["id"].astype(str))
    relation_ids = set(frames["relationships"]["id"].astype(str))
    community_entity_ids = values(frames["communities"]["entity_ids"])
    community_relation_ids = values(frames["communities"]["relationship_ids"])
    missing_entities = sorted(entity_ids - community_entity_ids)
    missing_relations = sorted(relation_ids - community_relation_ids)
    assert not missing_entities, missing_entities
    assert set(frames["communities"]["community"]) == set(frames["community_reports"]["community"])

    entities_by_id = frames["entities"].set_index("id")
    reports_by_community = frames["community_reports"].set_index("community")
    witness_coverage = []
    for _, community in frames["communities"].iterrows():
        report = reports_by_community.loc[community["community"]]
        content = str(report["full_content"])
        member_ids = [str(identity) for identity in community["entity_ids"]]
        missing_witnesses = []
        for identity in member_ids:
            entity = entities_by_id.loc[identity]
            witness = f"[Data: Entities ({entity['human_readable_id']})] {entity['type']} {entity['title']}：{entity['description']}"
            if witness not in content:
                missing_witnesses.append(identity)
        witness_coverage.append({
            "community": int(community["community"]),
            "member_count": len(member_ids),
            "witness_count": len(member_ids) - len(missing_witnesses),
            "missing_entity_ids": missing_witnesses,
        })
        assert not missing_witnesses, (community["community"], missing_witnesses)

    db = lancedb.connect(str(output_dir / "lancedb"))
    lance_tables = {}
    for table_name in sorted(db.list_tables().tables):
        table = db.open_table(table_name)
        field = table.schema.field("vector")
        dimensions = field.type.list_size
        lance_tables[table_name] = {"rows": table.count_rows(), "dimensions": dimensions}
        assert dimensions == 512, (table_name, dimensions)
        assert table.count_rows() > 0, table_name
    expected_lance = {
        "text_unit_text": len(frames["text_units"]),
        "entity_description": len(frames["entities"]),
        "community_full_content": len(frames["communities"]),
    }
    assert set(lance_tables) == set(expected_lance), lance_tables
    assert {name: row["rows"] for name, row in lance_tables.items()} == expected_lance

    manifest = json.loads((GRAPH_ROOT / "manifest.json").read_text())
    calls = manifest["calls"]
    usage = [call.get("usage") for call in calls if call.get("kind") == "completion"]
    report = {
        "graph_revision": manifest["graph_revision"],
        "graphrag_version": manifest["graphrag"],
        "provider_model": manifest["completion_model"],
        "provider_host": manifest["provider_host"],
        "source_counts": manifest["counts"],
        "output_table_rows": {name: len(frame) for name, frame in frames.items()},
        "entity_community_coverage": {
            "entity_count": len(entity_ids),
            "covered_count": len(entity_ids & community_entity_ids),
            "missing_ids": missing_entities,
        },
        "relationship_community_coverage": {
            "relationship_count": len(relation_ids),
            "covered_count": len(relation_ids & community_relation_ids),
            "missing_count": len(missing_relations),
        },
        "community_report_ids_match": True,
        "community_witness_coverage": {
            "community_count": len(witness_coverage),
            "member_count": sum(row["member_count"] for row in witness_coverage),
            "witness_count": sum(row["witness_count"] for row in witness_coverage),
            "all_members_have_witness": all(not row["missing_entity_ids"] for row in witness_coverage),
            "communities": witness_coverage,
        },
        "lance_tables": lance_tables,
        "completion_call_count": len(usage),
        "completion_usage_totals": {
            key: sum((value or {}).get(key, 0) or 0 for value in usage)
            for key in ("prompt_tokens", "completion_tokens", "total_tokens")
        },
        "implementation_hashes": manifest["implementation"],
        "fixture_hashes": manifest["files"],
        "manifest_path": str(GRAPH_ROOT / "manifest.json"),
    }
    assert report["community_witness_coverage"]["all_members_have_witness"]
    assert manifest["graph_revision"] == "ceres-recipe-byog-v3"
    assert manifest["community_grounding"] == "canonical-entity-witness-v1"
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
