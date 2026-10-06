from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.errors import AppError
from app.services.catalog_service import CatalogService

router = APIRouter(prefix='/api/v1', tags=['catalog'])


@router.get('/categories')
def categories(db: Session = Depends(get_db)):
    return CatalogService(db).get_categories()


@router.get('/products')
def products(q: str | None = None, category_id: str | None = None,
             page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=500),
             db: Session = Depends(get_db)):
    items, total = CatalogService(db).search_products(q=q, category_id=category_id, page=page, page_size=page_size)
    return {'items': items, 'total': total, 'page': page, 'page_size': page_size}


@router.get('/products/{sku_id}')
def product(sku_id: str, db: Session = Depends(get_db)):
    found = CatalogService(db).get_product(sku_id)
    if found is None:
        raise AppError(404, 'PRODUCT_NOT_FOUND', '未找到该商品')
    return found
