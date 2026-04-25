import logging
import time
from fastapi import Request

logger = logging.getLogger(__name__)

async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    msg = f"REQUEST {request.method} {request.url.path} {response.status_code} ({duration: .3f}s)"
    if response.status_code >= 500:
        logger.error(msg)
    elif response.status_code >= 400:
        logger.warning(msg)
    else:
        logger.info(msg)
    return response