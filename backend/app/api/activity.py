"""The existing homepage card enters the normal bounded shopping task."""
from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.identity import get_or_create_owner
from app.services.activity_service import enter_light_meal

router = APIRouter(prefix='/api/v1/guide/sessions/{session_id}/activities', tags=['guide'])


class ActivityEntry(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: str = Field(min_length=1, max_length=100)
    expected_task_id: str | None
    expected_state_version: int = Field(ge=0)
    expected_session_version: int = Field(ge=0)


@router.post('/light-meal')
def enter_activity(session_id: str, body: ActivityEntry, request: Request, response: Response, db: Session = Depends(get_db)):
    owner_id = get_or_create_owner(request, response, db)
    return enter_light_meal(db, owner_id, session_id, body.model_dump())
