"""Owner progress and a separately protected, minimal operator surface."""
import hmac
from typing import Literal
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db
from app.mercury.router import _owner
from app.human.models import HumanTicket
from app.human.service import owned_case, latest_ticket, ticket_view, create_ticket, append_message

router = APIRouter(prefix='/api/v1/mercury', tags=['human-support'])


def operator_only(x_internal_token: str | None = Header(default=None)):
    settings = get_settings()
    expected = settings.human_operator_token
    if (not expected or not x_internal_token or expected == settings.openai_api_key
            or not hmac.compare_digest(x_internal_token.encode(), expected.encode())):
        raise HTTPException(403, '需要独立的人工处理者凭据')


class RequestTicket(BaseModel):
    model_config = ConfigDict(extra='forbid')
    summary: str = Field(min_length=1, max_length=2000)

    @field_validator('summary')
    @classmethod
    def meaningful_summary(cls, value):
        if not value.strip():
            raise ValueError('请描述问题')
        return value.strip()


class MessageBody(BaseModel):
    model_config = ConfigDict(extra='forbid')
    content: str = Field(min_length=1, max_length=2000)
    version: int = Field(ge=1)

    @field_validator('content')
    @classmethod
    def meaningful_content(cls, value):
        if not value.strip():
            raise ValueError('请输入消息')
        return value.strip()


class UserMessage(MessageBody):
    ticket_id: str = Field(min_length=1)


class OperatorMessage(MessageBody):
    action: Literal['reply', 'ask', 'resolve', 'close']


@router.get('/sessions/{case_id}/human-ticket')
def get_ticket(case_id: str, owner_id: str = Depends(_owner), db: Session = Depends(get_db)):
    owned_case(db, owner_id, case_id)
    return ticket_view(db, latest_ticket(db, case_id))


@router.post('/sessions/{case_id}/human-ticket')
def request_ticket(case_id: str, body: RequestTicket, owner_id: str = Depends(_owner), db: Session = Depends(get_db)):
    case = owned_case(db, owner_id, case_id)
    ticket = create_ticket(db, case, body.summary, 'explicit_user_request')
    db.commit()
    return ticket_view(db, ticket)


@router.post('/sessions/{case_id}/human-ticket/messages')
def user_message(case_id: str, body: UserMessage, owner_id: str = Depends(_owner), db: Session = Depends(get_db)):
    owned_case(db, owner_id, case_id)
    ticket = latest_ticket(db, case_id)
    if ticket is None:
        raise HTTPException(404, '未找到工单')
    if ticket.ticket_id != body.ticket_id:
        raise HTTPException(409, '当前工单已变化，请刷新后重试')
    append_message(db, ticket, body.version, 'user', 'reply', body.content)
    db.commit()
    return ticket_view(db, ticket)


@router.get('/operator/tickets', dependencies=[Depends(operator_only)])
def operator_tickets(db: Session = Depends(get_db)):
    return [ticket_view(db, ticket) for ticket in db.scalars(select(HumanTicket).order_by(HumanTicket.created_at.desc()))]


@router.get('/operator/tickets/{ticket_id}/photos/{photo_id}', dependencies=[Depends(operator_only)])
def operator_photo(ticket_id: str, photo_id: str, db: Session = Depends(get_db)):
    from fastapi.responses import Response
    from app.mercury.models import MercuryCase
    from app.mercury.aftersales_models import AfterSalesPhoto
    ticket = db.get(HumanTicket, ticket_id)
    if ticket is None:
        raise HTTPException(404, '未找到工单')
    case = db.get(MercuryCase, ticket.case_id)
    photo = db.scalar(select(AfterSalesPhoto).where(AfterSalesPhoto.photo_id == photo_id,
        AfterSalesPhoto.case_id == case.case_id, AfterSalesPhoto.order_id == ticket.order_id,
        AfterSalesPhoto.owner_id == case.owner_id))
    if photo is None:
        raise HTTPException(404, '照片不属于该工单订单')
    return Response(photo.content, media_type=photo.content_type, headers={'X-Content-Type-Options':'nosniff'})


@router.post('/operator/tickets/{ticket_id}/messages', dependencies=[Depends(operator_only)])
def operator_message(ticket_id: str, body: OperatorMessage, db: Session = Depends(get_db)):
    ticket = db.get(HumanTicket, ticket_id)
    if ticket is None:
        raise HTTPException(404, '未找到工单')
    append_message(db, ticket, body.version, 'operator', body.action, body.content)
    db.commit()
    return ticket_view(db, ticket)
