from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db
from app.core.identity import get_or_create_owner
from app.core.errors import AppError
from app.models.store import Store

router = APIRouter(tags=['system'])


@router.get('/health')
def health(db: Session = Depends(get_db)):
    db.execute(text('SELECT 1'))
    return {'status': 'ok', 'database': 'connected', 'llm_configured': get_settings().is_live_llm_configured(), 'business_data_mode': 'demo'}


@router.get('/api/v1/bootstrap')
def bootstrap(request: Request, response: Response, db: Session = Depends(get_db)):
    store = db.get(Store, 'store-demo-01')
    if store is None:
        raise AppError(503, 'CATALOG_NOT_SEEDED', '尚未导入演示商品，请先运行静态数据导入。')
    owner_id = get_or_create_owner(request, response, db)
    settings = get_settings()
    return {'owner_id': owner_id, 'store_id': store.store_id,
            'delivery_zone_id': store.delivery_zone_id, 'llm_mode': settings.llm_mode,
            'business_data_mode': settings.business_data_mode,
            'demo_notice': '演示门店，价格、库存及配送为模拟数据'}
