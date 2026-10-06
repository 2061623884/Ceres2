"""Owner-scoped cart facts used by shelf commands and atomic checkout."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Cart(Base):
    __tablename__ = 'carts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('owners.id'), unique=True)
    store_id: Mapped[str] = mapped_column(ForeignKey('stores.store_id'))
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CartItem(Base):
    __tablename__ = 'cart_items'
    __table_args__ = (UniqueConstraint('cart_id', 'sku_id', name='uq_cart_sku'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey('carts.id'), index=True)
    sku_id: Mapped[str] = mapped_column(ForeignKey('catalog_products.sku_id'))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_fen: Mapped[int] = mapped_column(Integer)
