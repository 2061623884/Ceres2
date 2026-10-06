"""Minimal owner-scoped guide history and atomic turn receipts for TASK01."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class GuideSession(Base):
    __tablename__ = 'guide_sessions'
    session_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'), index=True)
    entry_context_json: Mapped[str] = mapped_column(Text, default='{}')
    current_task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    session_version: Mapped[int] = mapped_column(Integer, default=0)
    supply_store_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    delivery_zone_id: Mapped[str | None] = mapped_column(String(80), nullable=True)


class GuideTask(Base):
    __tablename__ = 'guide_tasks'
    task_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey('guide_sessions.session_id'), index=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'), index=True)
    state_version: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[str] = mapped_column(String(40), default='understanding')
    status: Mapped[str] = mapped_column(String(40), default='active')
    plan_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    conditions_json: Mapped[str] = mapped_column(Text, default='{}')


class GuideMessage(Base):
    __tablename__ = 'guide_messages'
    __table_args__ = (UniqueConstraint('session_id', 'sequence'),)
    message_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey('guide_sessions.session_id'), index=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'))
    task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    sequence: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(20))
    kind: Mapped[str] = mapped_column(String(20), default='text')
    content: Mapped[str] = mapped_column(Text)
    request_id: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class GuideTurnReceipt(Base):
    __tablename__ = 'guide_turn_receipts'
    __table_args__ = (UniqueConstraint('session_id', 'request_id'),)
    run_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey('guide_sessions.session_id'), index=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'))
    request_id: Mapped[str] = mapped_column(String(100))
    digest: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30), default='running')
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_json: Mapped[str] = mapped_column(Text, default='{}')
    anchor_json: Mapped[str] = mapped_column(Text, default='{}')
    execution_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    started_at: Mapped[float | None] = mapped_column(Float, nullable=True)


class GuideEntry(Base):
    """Stable owner entry; legacy sessions and their history remain untouched."""
    __tablename__ = 'guide_entries'
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey('guide_sessions.session_id'), unique=True)


class GuideCommandReceipt(Base):
    __tablename__ = 'guide_command_receipts'
    session_id: Mapped[str] = mapped_column(ForeignKey('guide_sessions.session_id'), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    digest: Mapped[str] = mapped_column(String(64))
    result_json: Mapped[str] = mapped_column(Text)


class GuideRunEvent(Base):
    __tablename__ = 'guide_run_events'
    run_id: Mapped[str] = mapped_column(ForeignKey('guide_turn_receipts.run_id'), primary_key=True)
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(40))
    payload_json: Mapped[str] = mapped_column(Text)
