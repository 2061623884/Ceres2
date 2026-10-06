"""Retained shelf client API; caller cannot choose owner or store."""
from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.business_mode import require_shopping_writes
from app.core.identity import get_or_create_owner
from app.services.cart_service import CartService

router = APIRouter(prefix='/api/v1', tags=['cart'])

class PatchItem(BaseModel):
    model_config = ConfigDict(extra='forbid')
    quantity: int = Field(ge=1)
    expected_cart_version: int = Field(ge=1)

class AddItem(PatchItem):
    sku_id: str = Field(min_length=1, max_length=64)


def service(request: Request, response: Response, db: Session = Depends(get_db)):
    return CartService(db, get_or_create_owner(request, response, db))

@router.get('/cart')
def get_cart(cart: CartService = Depends(service)):
    return cart.get_cart()

@router.post('/cart/items', dependencies=[Depends(require_shopping_writes)])
def add(body: AddItem, cart: CartService = Depends(service)):
    return cart.mutate(body.sku_id, body.quantity, body.expected_cart_version, 'add')

@router.patch('/cart/items/{sku_id}', dependencies=[Depends(require_shopping_writes)])
def patch(sku_id: str, body: PatchItem, cart: CartService = Depends(service)):
    return cart.mutate(sku_id, body.quantity, body.expected_cart_version, 'patch')

@router.delete('/cart/items/{sku_id}', dependencies=[Depends(require_shopping_writes)])
def remove(sku_id: str, expected_cart_version: int = Query(ge=1), cart: CartService = Depends(service)):
    return cart.mutate(sku_id, 0, expected_cart_version, 'remove')
