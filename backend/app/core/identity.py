"""Server-created anonymous owner identity; request bodies never choose it."""
from uuid import uuid4
from fastapi import Request, Response
from sqlalchemy.orm import Session
from app.models.identity import Owner

COOKIE_NAME = 'sg_owner_id'


def get_or_create_owner(request: Request, response: Response, db: Session) -> str:
    owner_id = request.cookies.get(COOKIE_NAME)
    if owner_id and db.get(Owner, owner_id) is not None:
        return owner_id
    owner_id = f'owner-{uuid4().hex}'
    db.add(Owner(id=owner_id))
    db.commit()
    response.set_cookie(COOKIE_NAME, owner_id, httponly=True, samesite='lax', secure=request.url.scheme == 'https', max_age=60 * 60 * 24 * 30)
    return owner_id
