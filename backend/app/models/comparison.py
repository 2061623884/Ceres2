"""Current, bounded, displayed candidates; never a purchase authorization."""
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ComparisonDisplay(Base):
    __tablename__ = 'comparison_displays'
    session_id: Mapped[str] = mapped_column(ForeignKey('guide_sessions.session_id'), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'))
    task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    session_version: Mapped[int] = mapped_column(Integer)
    state_version: Mapped[int] = mapped_column(Integer)
    context_json: Mapped[str] = mapped_column(Text)
    cards_json: Mapped[str] = mapped_column(Text)
    message_id: Mapped[str] = mapped_column(String(80))
