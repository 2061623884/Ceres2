"""Retained frontend error envelope."""
from typing import Any
from fastapi import HTTPException


class AppError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, retryable: bool = False, **extra: Any):
        super().__init__(status_code, {'error': {'code': code, 'message': message, 'retryable': retryable}, **extra})
