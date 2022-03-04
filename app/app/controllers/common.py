from typing import Any

from fastapi import HTTPException
from loguru import logger


def raise_http_exception(token: Any, status_code: int):
    logger.bind(
        error=token.get("error"),
        error_description=token.get("error_description"),
        correlation_id=token.get("correlation_id")
    ).error("Unauthorized")
    raise HTTPException(status_code=status_code)
