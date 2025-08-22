import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from src.infrastructure.config.logging_config import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and log details."""
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        
        # Start timing
        start_time = time.time()
        
        # Get client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "Unknown")
        
        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Client: {client_ip} - User-Agent: {user_agent[:100]}"
        )
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            # Calculate processing time for errors
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"Error: {type(e).__name__}: {str(e)} - "
                f"Time: {process_time:.3f}s"
            )
            
            # Re-raise the exception
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers (when behind proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to client host
        if request.client:
            return request.client.host
        
        return "Unknown"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware for detailed request/response logging."""
    
    def __init__(self, app, log_body: bool = False, max_body_size: int = 1024):
        super().__init__(app)
        self.log_body = log_body
        self.max_body_size = max_body_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request with detailed logging."""
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Log request details
        await self._log_request(request, request_id)
        
        # Add request ID to state
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response details
            await self._log_response(request, response, request_id, process_time)
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            logger.error(
                f"[{request_id}] Request failed - "
                f"Error: {type(e).__name__}: {str(e)} - "
                f"Time: {process_time:.3f}s"
            )
            
            raise
    
    async def _log_request(self, request: Request, request_id: str) -> None:
        """Log request details."""
        # Basic request info
        log_data = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client_ip": self._get_client_ip(request)
        }
        
        # Log request body if enabled
        if self.log_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    body_str = body.decode("utf-8")[:self.max_body_size]
                    log_data["body"] = body_str
                    if len(body) > self.max_body_size:
                        log_data["body_truncated"] = True
            except Exception as e:
                log_data["body_error"] = str(e)
        
        logger.debug(f"[{request_id}] Request: {log_data}")
    
    async def _log_response(self, request: Request, response: Response, 
                          request_id: str, process_time: float) -> None:
        """Log response details."""
        log_data = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "process_time": process_time
        }
        
        # Log response body if enabled and not streaming
        if self.log_body and not isinstance(response, StreamingResponse):
            try:
                if hasattr(response, 'body') and response.body:
                    body_str = response.body.decode("utf-8")[:self.max_body_size]
                    log_data["body"] = body_str
                    if len(response.body) > self.max_body_size:
                        log_data["body_truncated"] = True
            except Exception as e:
                log_data["body_error"] = str(e)
        
        logger.debug(f"[{request_id}] Response: {log_data}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "Unknown"