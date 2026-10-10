"""Public persisted role/opening contract. Navigation never performs business work."""
from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.identity import get_or_create_owner
from app.schemas.navigation import Role, RouteDecision, SelectedObject, SwitchRequest
from app.services import navigation_service as service

router = APIRouter(prefix='/api/v1/navigation/sessions/{session_id}', tags=['navigation'])


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')


class OpenRequest(Strict):
    role: Role


class RouteRequest(Strict):
    request_id: str = Field(min_length=1, max_length=80)
    opening_id: str
    role: Role
    message: str = Field(min_length=1, max_length=8000)
    selected_object: SelectedObject | None = None
    role_session_id: str | None = None


class DisplayRequest(Strict):
    opening_id: str
    routing_request_id: str


def owner(request: Request, response: Response, db: Session = Depends(get_db)):
    return get_or_create_owner(request, response, db)


@router.post('/opening')
def open_chat(session_id: str, body: OpenRequest, owner_id=Depends(owner), db: Session = Depends(get_db)):
    return service.open_chat(db, owner_id, session_id, body.role)


@router.get('/opening')
def read_chat(session_id: str, owner_id=Depends(owner), db: Session = Depends(get_db)):
    return service.read_opening(db, owner_id, session_id)


@router.delete('/opening/{opening_id}')
def close_chat(session_id: str, opening_id: str, owner_id=Depends(owner), db: Session = Depends(get_db)):
    return service.close_chat(db, owner_id, session_id, opening_id)


@router.post('/routes', response_model=RouteDecision)
def route_text(session_id: str, body: RouteRequest, owner_id=Depends(owner), db: Session = Depends(get_db)):
    return service.decide_route(db, owner_id, session_id, body.model_dump())


@router.post('/prompt-displayed')
def prompt_displayed(session_id: str, body: DisplayRequest, owner_id=Depends(owner), db: Session = Depends(get_db)):
    return service.displayed(db, owner_id, session_id, body.opening_id, body.routing_request_id)


@router.post('/switches')
def switch_role(session_id: str, body: SwitchRequest, owner_id=Depends(owner), db: Session = Depends(get_db)):
    return service.switch_role(db, owner_id, session_id, body.model_dump())
