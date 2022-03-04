from typing import Any

from fastapi import HTTPException
from loguru import logger


def raise_http_exception(token: Any, status_code: int, log_error_message: str):
    logger.bind(
        error=token.get("error"),
        error_description=token.get("error_description"),
        correlation_id=token.get("correlation_id")
    ).error(log_error_message)
    raise HTTPException(status_code=status_code, detail=log_error_message)
