"""Immutable proposals and atomic simulated application receipts, no copied orders."""
from sqlalchemy import Boolean, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AfterSalesProposal(Base):
    __tablename__ = 'aftersales_proposals'
    __table_args__ = (UniqueConstraint('case_id', 'revision'),)
    proposal_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'), index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey('mercury_cases.case_id'), index=True)
    order_id: Mapped[str] = mapped_column(ForeignKey('simulated_orders.order_id'))
    revision: Mapped[int] = mapped_column(Integer)
    selection_version: Mapped[int] = mapped_column(Integer)
    responsibility_generation: Mapped[int] = mapped_column(Integer)
    invalidated: Mapped[bool] = mapped_column(Boolean, default=False, server_default='0')
    facts_hash: Mapped[str] = mapped_column(String(64))
    preview_json: Mapped[str] = mapped_column(Text)


class AfterSalesApplication(Base):
    __tablename__ = 'aftersales_applications'
    __table_args__ = (UniqueConstraint('order_id', 'kind', 'item_scope'),)
    application_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'), index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey('mercury_cases.case_id'))
    proposal_id: Mapped[str] = mapped_column(ForeignKey('aftersales_proposals.proposal_id'), unique=True)
    order_id: Mapped[str] = mapped_column(ForeignKey('simulated_orders.order_id'))
    kind: Mapped[str] = mapped_column(String(16))
    item_scope: Mapped[str] = mapped_column(String(160))
    amount_fen: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))


class AfterSalesReceipt(Base):
    __tablename__ = 'aftersales_receipts'
    __table_args__ = (UniqueConstraint('owner_id', 'idempotency_key'),)
    receipt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'), index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey('mercury_cases.case_id'))
    proposal_id: Mapped[str] = mapped_column(ForeignKey('aftersales_proposals.proposal_id'), unique=True)
    application_id: Mapped[str] = mapped_column(ForeignKey('aftersales_applications.application_id'), unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(160))
    result_json: Mapped[str] = mapped_column(Text)


class AfterSalesPhoto(Base):
    __tablename__ = 'aftersales_photos'
    photo_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'), index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey('mercury_cases.case_id'), index=True)
    order_id: Mapped[str] = mapped_column(ForeignKey('simulated_orders.order_id'))
    selection_version: Mapped[int] = mapped_column(Integer)
    content_type: Mapped[str] = mapped_column(String(24))
    content: Mapped[bytes] = mapped_column(LargeBinary)
