import sys
import uuid

from loguru import logger

from app.core.setting import settings


def setup_logger():
    logger.bind().info("Setting up logger...")
    logger.remove()
    # prod mode
    if settings.LOG_SERIALIZE:
        logger.add(sys.stderr,
                   level=settings.LOG_LEVEL,
                   colorize=True,
                   serialize=settings.LOG_SERIALIZE)
    # dev mode
    else:
        logger.add(sys.stderr,
                   level=settings.LOG_LEVEL,
                   format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{extra}</level> - <yellow>{message}</yellow>",
                   colorize=True,
                   serialize=settings.LOG_SERIALIZE)


# setup_logger()


async def generate_trace_id() -> uuid.UUID:
    # This function (uuid4) guarantees the random no. and doesn’t compromise with privacy.
    trace_id: uuid.UUID = uuid.uuid4()
    return trace_id
