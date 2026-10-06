"""Canonical four-category memory; tombstones fence later background work."""
from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ShoppingMemory(Base):
    __tablename__ = 'shopping_memories'
    __table_args__ = (
        CheckConstraint("category IN ('user','feedback','project','reference')"),
        CheckConstraint("domain IN ('shopping','aftersales','communication')"),
        CheckConstraint("source IN ('explicit','automatic')"),
        CheckConstraint("origin_role IN ('keke','momo')"),
        CheckConstraint('revision >= 1'),
    )
    memory_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'), index=True)
    category: Mapped[str] = mapped_column(String(20))
    domain: Mapped[str] = mapped_column(String(20))
    key: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20))
    origin_role: Mapped[str] = mapped_column(String(20))
    source_id: Mapped[str] = mapped_column(String(100))
    source_quote: Mapped[str] = mapped_column(Text)
    reference_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[float] = mapped_column(Float)
    expires_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    deleted_at: Mapped[float | None] = mapped_column(Float, nullable=True)


class MemoryJob(Base):
    """One immutable published source and its recoverable extraction result."""
    __tablename__ = 'memory_jobs'
    __table_args__ = (
        UniqueConstraint('owner_id', 'kind', 'source_id'),
        Index('one_active_memory_dream', 'owner_id', unique=True,
              sqlite_where=text("kind = 'dream' AND status IN ('pending','running')")),
        CheckConstraint("kind IN ('extract','dream')"),
        CheckConstraint("status IN ('pending','running','completed','failed')"),
    )
    job_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    source_id: Mapped[str] = mapped_column(String(100))
    source_json: Mapped[str] = mapped_column(Text)
    versions_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    lease_token: Mapped[str | None] = mapped_column(String(80), nullable=True)
    lease_until: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[float] = mapped_column(Float)
    completed_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
