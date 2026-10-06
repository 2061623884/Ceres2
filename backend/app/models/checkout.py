"""Checkout intent and committed result share the order/cart transaction."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class CheckoutPreview(Base):
    __tablename__ = 'checkout_previews'
    preview_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'), index=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey('carts.id'))
    cart_version: Mapped[int] = mapped_column(Integer)
    snapshot_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CheckoutReceipt(Base):
    __tablename__ = 'checkout_receipts'
    __table_args__ = (UniqueConstraint('owner_id', 'idempotency_key', name='uq_checkout_key'),)
    receipt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    preview_id: Mapped[str] = mapped_column(ForeignKey('checkout_previews.preview_id'), unique=True)
    order_id: Mapped[str] = mapped_column(ForeignKey('simulated_orders.order_id'), unique=True)
    result_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
