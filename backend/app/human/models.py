"""Additive ticket records in the canonical business database."""
from sqlalchemy import ForeignKey, Integer, String, Text, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class HumanTicket(Base):
    __tablename__ = 'human_tickets'
    ticket_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey('mercury_cases.case_id'), index=True)
    order_id: Mapped[str | None] = mapped_column(ForeignKey('simulated_orders.order_id'), nullable=True)
    reason: Mapped[str] = mapped_column(String(32))
    summary: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default='open')
    generation: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer, default=1)
    history_json: Mapped[str] = mapped_column(Text)
    messages_json: Mapped[str] = mapped_column(Text, default='[]')
    created_at: Mapped[str] = mapped_column(String(40))
    __table_args__ = (Index('uq_human_open_case', 'case_id', unique=True,
        sqlite_where=text("status IN ('open', 'waiting_user')"),
        postgresql_where=text("status IN ('open', 'waiting_user')")),)


class HumanHandoffState(Base):
    __tablename__ = 'human_handoff_states'
    case_id: Mapped[str] = mapped_column(ForeignKey('mercury_cases.case_id'), primary_key=True)
    selection_version: Mapped[int] = mapped_column(Integer)
    service_failures: Mapped[int] = mapped_column(Integer, default=0)
