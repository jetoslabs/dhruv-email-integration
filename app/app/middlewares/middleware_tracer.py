import random
import string
import time

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from app.schemas.schema_log import LogSchema


class TracerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        trace = ''.join(random.choices(string.hexdigits, k=9))
        logger.bind(log=LogSchema(trace_id=trace, scope="tracer").dict(),
                    request_path=request.url.path).info("Start request")

        start_time = time.time()
        request.scope.update(trace_id=trace)  # passing trace id in request
        response = await call_next(request)
        response_time_ms = round((time.time() - start_time) * 1000, 2)

        logger.bind(log=LogSchema(trace_id=trace, scope="tracer").dict(),
                    response_time_ms=response_time_ms,
                    status_code=response.status_code).info("Finish request")
        return response
