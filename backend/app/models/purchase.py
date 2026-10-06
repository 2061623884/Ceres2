"""Durable confirmation receipts and per-task added quantities."""
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class PurchaseConfirmation(Base):
    __tablename__ = 'purchase_confirmations'
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'), primary_key=True)
    request_key: Mapped[str] = mapped_column(String(150), primary_key=True)
    digest: Mapped[str] = mapped_column(String(64))
    task_id: Mapped[str] = mapped_column(ForeignKey('guide_tasks.task_id'), index=True)
    plan_id: Mapped[str] = mapped_column(String(80))
    plan_version: Mapped[int] = mapped_column(Integer)
    result_json: Mapped[str] = mapped_column(Text)


class PurchaseLedger(Base):
    __tablename__ = 'purchase_ledger'
    task_id: Mapped[str] = mapped_column(ForeignKey('guide_tasks.task_id'), primary_key=True)
    sku_id: Mapped[str] = mapped_column(ForeignKey('catalog_products.sku_id'), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'))
    added_quantity: Mapped[int] = mapped_column(Integer)
