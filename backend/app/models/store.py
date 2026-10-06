"""Store and its canonical mutable offers, separate from SKU facts."""
from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Store(Base):
    __tablename__ = 'stores'
    store_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    is_demo: Mapped[bool] = mapped_column(default=True)
    delivery_zone_id: Mapped[str] = mapped_column(String(64))
    delivery_reachable: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)
    delivery_version: Mapped[int] = mapped_column(Integer, default=1, server_default='1')


class Offer(Base):
    __tablename__ = 'offers'
    __table_args__ = (UniqueConstraint('store_id', 'sku_id', name='uq_store_sku'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[str] = mapped_column(ForeignKey('stores.store_id'), index=True)
    sku_id: Mapped[str] = mapped_column(ForeignKey('catalog_products.sku_id'), index=True)
    price_fen: Mapped[int] = mapped_column(Integer)
    available_qty: Mapped[int] = mapped_column(Integer)
    sellable: Mapped[bool] = mapped_column(default=True)
    offer_version: Mapped[int] = mapped_column(Integer, default=1)
    is_demo: Mapped[bool] = mapped_column(default=True)
