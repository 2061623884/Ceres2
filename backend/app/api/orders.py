"""Owner-scoped simulated checkout requires an explicit confirmation command."""
from typing import Literal
from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.business_mode import require_shopping_writes
from app.core.identity import get_or_create_owner
from app.services.checkout_service import CheckoutService

router = APIRouter(prefix='/api/v1', tags=['simulated-orders'])

class PreviewRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_cart_version: int = Field(ge=1)

class ConfirmRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    preview_id: str = Field(min_length=1, max_length=64)
    idempotency_key: str = Field(min_length=1, max_length=128)
    confirmed: Literal[True]

class DemoAdvance(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_version: int = Field(ge=1)
    status: Literal['shipped', 'delivered']


def service(request: Request, response: Response, db: Session = Depends(get_db)):
    return CheckoutService(db, get_or_create_owner(request, response, db))

@router.post('/checkout/preview', dependencies=[Depends(require_shopping_writes)])
def preview(body: PreviewRequest, checkout: CheckoutService = Depends(service)):
    return checkout.preview(body.expected_cart_version)

@router.post('/checkout/confirm', dependencies=[Depends(require_shopping_writes)])
def confirm(body: ConfirmRequest, checkout: CheckoutService = Depends(service)):
    return checkout.confirm(body.preview_id, body.idempotency_key)

@router.get('/orders')
def list_orders(checkout: CheckoutService = Depends(service)):
    return checkout.list_orders()

@router.get('/orders/{order_id}')
def get_order(order_id: str, checkout: CheckoutService = Depends(service)):
    return checkout.get_order(order_id)

@router.post('/orders/{order_id}/demo-state', dependencies=[Depends(require_shopping_writes)])
def advance_demo(order_id: str, body: DemoAdvance, checkout: CheckoutService = Depends(service)):
    return checkout.advance_demo(order_id, body.expected_version, body.status)
