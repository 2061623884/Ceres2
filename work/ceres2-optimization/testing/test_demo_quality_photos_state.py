"""End-to-end HTTP checks for demo order progression and quality/photo handoff."""

from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

pytest_plugins = ["test_order_case_journey"]

from test_order_case_journey import journey  # noqa: E402,F401


REPORT = Path(__file__).with_name("demo-quality-photos-state-smoke-2026-10-07.json")
SKU = "demo:shrimp-200g"
PNG = base64.b64encode(
    bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489")
).decode("ascii")


def make_order(client):
    cart = client.get("/api/v1/cart").json()
    added = client.post("/api/v1/cart/items", json={
        "sku_id": SKU,
        "quantity": 2,
        "expected_cart_version": cart["version"],
    })
    assert added.status_code == 200, added.text
    cart = added.json()
    preview = client.post("/api/v1/checkout/preview", json={
        "expected_cart_version": cart["version"],
    })
    assert preview.status_code == 200, preview.text
    confirmed = client.post("/api/v1/checkout/confirm", json={
        "preview_id": preview.json()["preview_id"],
        "idempotency_key": "quality-demo-order",
        "confirmed": True,
    })
    assert confirmed.status_code == 200, confirmed.text
    return confirmed.json()["order"]


def error_code(response):
    return response.json().get("error", {}).get("code")


def test_demo_state_and_quality_photo_boundaries(journey, monkeypatch):
    from app.core.config import get_settings
    from app.human.models import HumanTicket
    from app.mercury.aftersales_models import AfterSalesApplication, AfterSalesPhoto, AfterSalesReceipt
    from app.mercury.models import SimulatedOrder

    client, make_client = journey
    order = make_order(client)
    item = order["items"][0]
    assert item["sku_id"] == SKU and item["quantity"] == 2
    assert item["returnable"] is False
    original_snapshot = {key: order[key] for key in ("store_id", "items", "total_fen")}

    created_case = client.post("/api/v1/mercury/sessions")
    assert created_case.status_code == 200, created_case.text
    case_id = created_case.json()["session_id"]
    case_path = f"/api/v1/mercury/sessions/{case_id}"
    selected = client.put(case_path + "/order", json={"order_id": order["order_id"], "selection_version": 0})
    assert selected.status_code == 200, selected.text
    selection_version = selected.json()["selection_version"]

    before_delivery = client.post(case_path + "/proposals", json={
        "kind": "quality", "item_id": SKU, "reason": "外包装破损", "selection_version": selection_version,
        "problem_quantity": 1,
    })
    assert before_delivery.status_code == 409 and error_code(before_delivery) == "NOT_DELIVERED"

    submitted_to_shipped = client.post(f"/api/v1/orders/{order['order_id']}/demo-state", json={
        "expected_version": 1, "status": "shipped",
    })
    assert submitted_to_shipped.status_code == 200, submitted_to_shipped.text
    shipped = submitted_to_shipped.json()
    assert (shipped["status"], shipped["version"]) == ("shipped", 2)
    stale_delivery = client.post(f"/api/v1/orders/{order['order_id']}/demo-state", json={
        "expected_version": 1, "status": "delivered",
    })
    assert stale_delivery.status_code == 409 and error_code(stale_delivery) == "ORDER_STATE_CHANGED"
    shipped_to_delivered = client.post(f"/api/v1/orders/{order['order_id']}/demo-state", json={
        "expected_version": 2, "status": "delivered",
    })
    assert shipped_to_delivered.status_code == 200, shipped_to_delivered.text
    delivered = shipped_to_delivered.json()
    assert (delivered["status"], delivered["version"]) == ("delivered", 3)
    assert delivered["delivered_at"]
    assert {key: delivered[key] for key in original_snapshot} == original_snapshot
    stale_shipment = client.post(f"/api/v1/orders/{order['order_id']}/demo-state", json={
        "expected_version": 3, "status": "shipped",
    })
    assert stale_shipment.status_code == 409 and error_code(stale_shipment) == "ORDER_STATE_CHANGED"
    assert client.get(f"/api/v1/orders/{order['order_id']}").json() == delivered

    wrong_signature = client.post(case_path + "/photos", json={
        "content_type": "image/jpeg", "data_base64": PNG, "selection_version": selection_version,
    })
    assert wrong_signature.status_code == 422 and error_code(wrong_signature) == "PHOTO_INVALID"
    oversized = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"x" * (4 * 1024 * 1024 - 7)).decode("ascii")
    too_large = client.post(case_path + "/photos", json={
        "content_type": "image/png", "data_base64": oversized, "selection_version": selection_version,
    })
    assert too_large.status_code == 422 and error_code(too_large) == "PHOTO_INVALID"

    uploaded = client.post(case_path + "/photos", json={
        "content_type": "image/png", "data_base64": PNG, "selection_version": selection_version,
    })
    assert uploaded.status_code == 200, uploaded.text
    photo_id = uploaded.json()["photo_id"]
    stale_photo = client.post(case_path + "/photos", json={
        "content_type": "image/png", "data_base64": PNG, "selection_version": selection_version - 1,
    })
    assert stale_photo.status_code == 409 and error_code(stale_photo) == "STALE_SELECTION"

    def propose(*, quantity=1, photos=None, version=selection_version):
        return client.post(case_path + "/proposals", json={
            "kind": "quality", "item_id": SKU, "reason": "外包装破损", "selection_version": version,
            "problem_quantity": quantity, "photo_ids": photos or [],
        })

    too_many = propose(quantity=3)
    assert too_many.status_code == 422 and error_code(too_many) == "PROBLEM_QUANTITY_INVALID"
    stale_proposal = propose(version=selection_version + 1)
    assert stale_proposal.status_code == 409 and error_code(stale_proposal) == "STALE_SELECTION"
    foreign_photo = propose(photos=["photo-from-another-owner-or-case"])
    assert foreign_photo.status_code == 422 and error_code(foreign_photo) == "PHOTO_SCOPE_INVALID"

    proposal = propose(photos=[photo_id])
    assert proposal.status_code == 200, proposal.text
    preview = proposal.json()
    assert preview["status"] == "awaiting_confirmation"
    assert preview["kind"] == "quality" and preview["problem_quantity"] == 1
    assert preview["photo_ids"] == [photo_id]
    assert "不阻止质量问题登记" in preview["policy"]
    assert client.get(case_path + "/aftersales").json()["receipts"] == []

    confirmed = client.post(case_path + "/confirm", json={
        "proposal_id": preview["proposal_id"], "idempotency_key": "quality-demo-confirm-1", "confirmed": True,
    })
    assert confirmed.status_code == 200, confirmed.text
    receipt = confirmed.json()
    assert receipt["status"] == "requested" and receipt["simulated"] is True
    assert receipt["kind"] == "quality" and receipt["problem_quantity"] == 1
    assert client.post(case_path + "/confirm", json={
        "proposal_id": preview["proposal_id"], "idempotency_key": "quality-demo-confirm-1", "confirmed": True,
    }).json() == receipt
    aftersales = client.get(case_path + "/aftersales").json()
    assert len(aftersales["receipts"]) == 1
    assert aftersales["receipts"][0] == receipt

    homeowner_photo = client.get(case_path + f"/photos/{photo_id}")
    assert homeowner_photo.status_code == 200 and homeowner_photo.content.startswith(b"\x89PNG\r\n\x1a\n")
    ticket_view = client.get(case_path + "/human-ticket")
    assert ticket_view.status_code == 200
    ticket = ticket_view.json()
    assert ticket["order_id"] == order["order_id"]
    assert ticket["reason"] == "quality_application"
    assert [photo["photo_id"] for photo in ticket["photos"]] == [photo_id]
    assert ticket["applications"][0]["receipt_id"] == receipt["receipt_id"]

    owner_id = client.get("/api/v1/bootstrap").json()["owner_id"]
    with make_client() as other_client:
        other_owner = other_client.get("/api/v1/bootstrap").json()["owner_id"]
        assert other_owner != owner_id
        foreign_read = other_client.get(case_path + f"/photos/{photo_id}")
        assert foreign_read.status_code == 404

    token = "tester-only-independent-operator-token"
    monkeypatch.setattr(get_settings(), "human_operator_token", token)
    assert client.get(f"/api/v1/mercury/operator/tickets/{ticket['ticket_id']}/photos/{photo_id}").status_code == 403
    assert client.get(f"/api/v1/mercury/operator/tickets/{ticket['ticket_id']}/photos/{photo_id}",
                      headers={"X-Internal-Token": token}).content == homeowner_photo.content
    assert client.get(f"/api/v1/mercury/operator/tickets/not-this-ticket/photos/{photo_id}",
                      headers={"X-Internal-Token": token}).status_code == 404

    # The owner view exposes the durable receipt and photo; the operator view exposes its linked ticket.
    REPORT.write_text(json.dumps({
        "order_id": order["order_id"],
        "sku_id": SKU,
        "returnable": item["returnable"],
        "state_versions": [
            {"status": "submitted", "version": 1},
            {"status": "shipped", "version": shipped["version"]},
            {"status": "delivered", "version": delivered["version"]},
        ],
        "snapshot_unchanged": {key: delivered[key] == value for key, value in original_snapshot.items()},
        "quality_quantity": receipt["problem_quantity"],
        "photo_id": photo_id,
        "application_id": receipt["application_id"],
        "receipt_id": receipt["receipt_id"],
        "ticket_id": ticket["ticket_id"],
        "quality_confirmation_replay_equal": True,
        "stale_state_rejected": stale_delivery.status_code == 409 and stale_shipment.status_code == 409,
        "out_of_owner_photo_read_status": foreign_read.status_code,
        "operator_without_token_status": 403,
        "operator_scoped_photo_status": 200,
        "wrong_ticket_photo_status": 404,
        "oversize_photo_rejected": too_large.status_code == 422,
        "wrong_signature_rejected": wrong_signature.status_code == 422,
        "sample_is_demo_not_real_fulfillment": receipt["simulated"] is True,
    }, ensure_ascii=False, indent=2) + "\n")
