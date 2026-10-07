"""Public HTTP smoke for Unicode text in the Base64 upload field."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[3]
TMP = Path(__file__).resolve().parent / "tmp" / "unicode-photo-422"
TMP.mkdir(parents=True, exist_ok=True)

import sys

sys.path.insert(0, str(ROOT / "backend"))

from app.core.database import create_db_engine, get_db, init_db  # noqa: E402
from app.main import create_app  # noqa: E402


def main() -> None:
    engine = create_db_engine(f"sqlite:///{TMP / 'business.sqlite3'}")
    init_db(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    app = create_app(database_engine=engine)

    def database():
        with sessions() as db:
            yield db

    app.dependency_overrides[get_db] = database
    with TestClient(app, raise_server_exceptions=False) as client:
        client.get("/api/v1/bootstrap")
        session_id = client.post("/api/v1/mercury/sessions").json()["session_id"]
        response = client.post(
            f"/api/v1/mercury/sessions/{session_id}/photos",
            json={
                "content_type": "image/png",
                "data_base64": "照片不是合法的Base64",
                "selection_version": 0,
            },
        )
    engine.dispose()
    payload = response.json()
    result = {
        "status_code": response.status_code,
        "error_code": payload.get("error", {}).get("code"),
        "unicode_payload_rejected_as_422": response.status_code == 422,
        "database_worktree_local": True,
        "provider_credentials_used": False,
    }
    assert result["unicode_payload_rejected_as_422"]
    assert result["error_code"] == "PHOTO_INVALID", payload
    (Path(__file__).resolve().parent / "unicode-photo-422-smoke-2026-10-07.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
