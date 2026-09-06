import time
import logging
import json
from typing import Callable, Awaitable
from fastapi import Request, Response

logger = logging.getLogger("dataforge.telemetry")

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        if hasattr(record, "telemetry"):
            log_obj.update(record.telemetry)
        
        return json.dumps(log_obj)

def setup_telemetry():
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Remove existing handlers to avoid duplicates
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(handler)
    
    # Specifically quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

async def telemetry_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time_ms = (time.time() - start_time) * 1000
    
    logger.info("Request completed", extra={
        "telemetry": {
            "type": "http_request",
            "method": request.method,
            "url": str(request.url.path),
            "status_code": response.status_code,
            "duration_ms": round(process_time_ms, 2)
        }
    })
    
    # Add a custom header for tracing/debugging
    response.headers["X-Process-Time-Ms"] = str(round(process_time_ms, 2))
    return response
