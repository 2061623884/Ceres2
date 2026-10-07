"""Check repeatable static fixture import against a worktree-local temporary DB."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.database import Base  # noqa: E402
from app.models.catalog import CatalogProduct  # noqa: E402
from app.models.store import Offer, Store  # noqa: E402
from app.services.seed_service import seed_catalog  # noqa: E402


def counts(session: Session) -> dict[str, int]:
    return {
        "stores": session.scalar(select(func.count()).select_from(Store)),
        "products": session.scalar(select(func.count()).select_from(CatalogProduct)),
        "offers": session.scalar(select(func.count()).select_from(Offer)),
    }


def main() -> None:
    fixtures = ROOT / "data" / "fixtures"
    offers_fixture = json.loads((fixtures / "offers.json").read_text())
    expected = {
        "stores": 1,
        "products": len(json.loads((fixtures / "products.json").read_text())["products"]),
        "offers": len(offers_fixture["offers"]),
    }
    with TemporaryDirectory(prefix="import-smoke-", dir=Path(__file__).parent) as temp_dir:
        db_path = Path(temp_dir) / "catalog.sqlite3"
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        with Session(engine) as session, session.begin():
            seed_catalog(session, fixtures)
        with Session(engine) as session, session.begin():
            first = counts(session)
            assert first == expected, (first, expected)
            offer = session.scalar(select(Offer).order_by(Offer.id).limit(1))
            offer_id = offer.id
            offer.price_fen = 271
            offer.available_qty = 3
        with Session(engine) as session, session.begin():
            seed_catalog(session, fixtures)
        with Session(engine) as session:
            second = counts(session)
            retained = session.get(Offer, offer_id)
            mutable_facts_preserved = retained.price_fen == 271 and retained.available_qty == 3
        engine.dispose()
        assert second == first, (first, second)
        assert mutable_facts_preserved
        print(json.dumps({
            "first_import_counts": first,
            "repeat_import_counts": second,
            "counts_unchanged": second == first,
            "mutable_offer_facts_preserved": mutable_facts_preserved,
            "database_temporary_and_worktree_local": True,
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
