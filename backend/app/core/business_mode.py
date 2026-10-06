"""Bounded shopping-write hold; not a database-wide read-only mode."""
from app.core.config import get_settings
from app.core.errors import AppError


def require_shopping_writes() -> None:
    if get_settings().shopping_writes_paused:
        raise AppError(503, 'SHOPPING_WRITES_PAUSED', '购物车和模拟结算写入暂时停用，已有数据仍可查看。')
