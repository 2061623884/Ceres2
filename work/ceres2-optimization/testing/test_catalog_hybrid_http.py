"""Real demo corpus through HTTP catalog and deterministic comparison filters."""

import json
import math
from pathlib import Path

import pytest
from sqlalchemy import select

pytest_plugins = ["test_foundation_http"]


TARGET = "demo:shrimp-200g"
QUERY = "炒饭用的虾仁"
REPORT = Path(__file__).with_name("catalog-hybrid-http-smoke-2026-10-07.json")


def test_demo_catalog_http_returns_real_hybrid_evidence_and_current_offer(web):
    client, sessions = web
    listing = client.get("/api/v1/products", params={"page_size": 500})
    assert listing.status_code == 200
    assert listing.json()["total"] == 71 and len(listing.json()["items"]) == 71

    result = client.get("/api/v1/products", params={"q": QUERY, "page_size": 100})
    assert result.status_code == 200, result.text
    target = next(row for row in result.json()["items"] if row["sku_id"] == TARGET)
    retrieval = target["retrieval"]
    assert retrieval["source"] == {"file": "products.json", "record_id": TARGET}
    assert {"sparse", "dense"}.issubset(retrieval["ranks"])
    assert {"sparse", "dense"}.issubset(retrieval["scores"])
    assert math.isclose(
        retrieval["rrf_score"],
        sum(1 / (60 + rank) for rank in retrieval["ranks"].values()),
        rel_tol=0,
        abs_tol=1e-15,
    )
    assert retrieval["corpus_revision"]
    report = {
        "catalog_count": listing.json()["total"],
        "query": QUERY,
        "target_sku": TARGET,
        "target_source": retrieval["source"],
        "target_ranks": retrieval["ranks"],
        "target_scores": retrieval["scores"],
        "target_rrf_score": retrieval["rrf_score"],
        "corpus_revision": retrieval["corpus_revision"],
        "rrf_formula_matches": True,
    }

    with sessions() as db:
        from app.models.store import Offer

        offer = db.scalar(select(Offer).where(Offer.store_id == "store-demo-01", Offer.sku_id == TARGET))
        offer.price_fen = 1777
        offer.available_qty = 3
        offer.offer_version += 1
        db.commit()

    refreshed = client.get("/api/v1/products", params={"q": QUERY, "page_size": 100}).json()
    current = next(row for row in refreshed["items"] if row["sku_id"] == TARGET)
    assert (current["price_fen"], current["available_qty"], current["offer_version"]) == (1777, 3, 2)
    assert current["retrieval"] == retrieval  # current commercial values are read after RAG retrieval
    report["offer_before"] = {"price_fen": target["price_fen"], "available_qty": target["available_qty"], "offer_version": target["offer_version"]}
    report["offer_after"] = {"price_fen": current["price_fen"], "available_qty": current["available_qty"], "offer_version": current["offer_version"]}
    report["retrieval_evidence_stable_after_offer_change"] = current["retrieval"] == retrieval

    unknown_count = client.get("/api/v1/products", params={"q": "苹果"}).json()["total"]
    wrong_category_count = client.get("/api/v1/products", params={"q": QUERY, "category_id": "fruit"}).json()["total"]
    assert unknown_count == 0
    assert wrong_category_count == 0
    report["unknown_query_count"] = unknown_count
    report["wrong_category_count"] = wrong_category_count
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


def test_comparison_applies_product_type_and_budget_to_current_rag_candidates(web):
    client, sessions = web
    bootstrap = client.get("/api/v1/bootstrap").json()
    created = client.post(
        "/api/v1/guide/sessions",
        json={"entry_context": {"page": "home", "store_id": bootstrap["store_id"], "delivery_zone_id": bootstrap["delivery_zone_id"]}},
    )
    assert created.status_code == 200, created.text
    session_id = created.json()["session_id"]
    session_path = f"/api/v1/guide/sessions/{session_id}"

    def command(kind, request_id, *, goal=None, conditions=None):
        snapshot = client.get(session_path).json()
        return client.post(session_path + "/tasks/current", json={
            "request_id": request_id,
            "kind": kind,
            "goal": goal,
            "conditions": conditions,
            "expected_task_id": snapshot["task_id"],
            "expected_state_version": snapshot["state_version"],
            "expected_session_version": snapshot["session_version"],
        })

    started = command("new_goal", "hybrid-goal", goal="选炒饭用的虾仁", conditions={
        "category_id": "seafood", "product_type": "shrimp", "budget_fen": 1600,
    })
    assert started.status_code == 200, started.text

    with sessions() as db:
        from app.models.store import Offer
        from app.services.comparison_service import ComparisonService

        offer = db.scalar(select(Offer).where(Offer.store_id == "store-demo-01", Offer.sku_id == TARGET))
        offer.price_fen = 1777
        offer.available_qty = 3
        offer.offer_version += 1
        db.commit()
        candidates, count = ComparisonService(db, bootstrap["owner_id"]).search(
            session_id, {"query": QUERY}, scope_to_page=False,
        )
        assert count == 0 and candidates == []  # current Offer exceeds the explicit budget
        budget_below_current_offer = {"budget_fen": 1600, "current_price_fen": offer.price_fen, "result_count": count}

    amended = command("amend", "hybrid-budget-update", conditions={"budget_fen": 2000})
    assert amended.status_code == 200, amended.text
    with sessions() as db:
        from app.services.comparison_service import ComparisonService

        candidates, count = ComparisonService(db, bootstrap["owner_id"]).search(
            session_id, {"query": QUERY}, scope_to_page=False,
        )
        assert count == 1 and len(candidates) == 1
        product = candidates[0]
        assert product["sku_id"] == TARGET
        assert product["product_type"] == "shrimp"
        assert product["price_fen"] == 1777
        assert "retrieval" in product and product["retrieval"]["source"]["record_id"] == TARGET
        report = json.loads(REPORT.read_text())
        report["comparison_filter"] = {
            "product_type": "shrimp",
            "category_id": "seafood",
            "below_budget": budget_below_current_offer,
            "raised_budget_fen": 2000,
            "returned_count": count,
            "returned_sku": product["sku_id"],
            "returned_current_price_fen": product["price_fen"],
            "source_record_id": product["retrieval"]["source"]["record_id"],
        }
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
