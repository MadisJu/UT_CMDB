import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.core.logging_adapter import get_logger

class APILoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("api")

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            process_time = time.time() - start_time
            
            log_payload = {
                "event_type": "api_request",
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "status_code": status_code,
                "duration_ms": round(process_time * 1000, 2)
            }
            
            self.logger.info(
                f"{request.method} {request.url.path} - {status_code}", 
                extra={"extra_data": log_payload}
            )
            
        return response
