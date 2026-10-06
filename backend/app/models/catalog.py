"""Only catalog facts used by browsing and grounded product queries."""
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class CatalogProduct(Base):
    __tablename__ = 'catalog_products'
    sku_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    name_zh: Mapped[str | None] = mapped_column(String(256))
    category_id: Mapped[str] = mapped_column(String(32), index=True)
    brand: Mapped[str | None] = mapped_column(String(128))
    image_path: Mapped[str | None] = mapped_column(String(512))
    source: Mapped[str] = mapped_column(String(32), default='demo')
    review_status: Mapped[str] = mapped_column(String(32), default='approved')
    spec_quantity: Mapped[float | None]
    spec_unit: Mapped[str | None] = mapped_column(String(16))
    ingredient_ids: Mapped[str] = mapped_column(Text, default='[]')
    usage_tags: Mapped[str] = mapped_column(Text, default='[]')
    product_type: Mapped[str | None] = mapped_column(String(32))
    metadata_json: Mapped[str] = mapped_column(Text, default='{}')
