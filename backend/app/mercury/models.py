"""Canonical query-slice facts, in the shared SQLAlchemy business database."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class SimulatedOrder(Base):
    __tablename__ = 'simulated_orders'
    order_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'), index=True)
    store_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default='1')
    status: Mapped[str] = mapped_column(String(32))
    snapshot_json: Mapped[str] = mapped_column(Text)
    total_fen: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MercuryCase(Base):
    __tablename__ = 'mercury_cases'
    case_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'), index=True)
    order_id: Mapped[str | None] = mapped_column(ForeignKey('simulated_orders.order_id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    selection_version: Mapped[int] = mapped_column(Integer, default=0)
    aftersales_intent_version: Mapped[int] = mapped_column(Integer, default=0, server_default='0')
    responsibility: Mapped[str] = mapped_column(String(16), default='agent')
    responsibility_generation: Mapped[int] = mapped_column(Integer, default=0)
    active_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    active_until: Mapped[float | None] = mapped_column(Float, nullable=True)
    messages_json: Mapped[str] = mapped_column(Text, default='[]')
    query_status: Mapped[str] = mapped_column(String(32), default='ready')
    tool_rounds: Mapped[int] = mapped_column(Integer, default=0)
