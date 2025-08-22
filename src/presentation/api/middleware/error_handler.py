from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
from typing import Union
from datetime import datetime

from src.infrastructure.config.logging_config import get_logger
from src.presentation.api.models.response_models import ErrorResponse

logger = get_logger(__name__)


def add_error_handlers(app: FastAPI) -> None:
    """Add error handlers to the FastAPI application."""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions."""
        logger.warning(
            f"HTTP exception: {exc.status_code} - {exc.detail} - "
            f"Path: {request.url.path} - Method: {request.method}"
        )
        
        error_data = {
            "success": False,
            "message": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "status_code": exc.status_code,
                "path": str(request.url.path),
                "method": request.method
            }
        }
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_data
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(
        request: Request, 
        exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle Starlette HTTP exceptions."""
        logger.warning(
            f"Starlette HTTP exception: {exc.status_code} - {exc.detail} - "
            f"Path: {request.url.path} - Method: {request.method}"
        )
        
        error_data = {
            "success": False,
            "message": str(exc.detail),
            "error_code": f"HTTP_{exc.status_code}",
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "status_code": exc.status_code,
                "path": str(request.url.path),
                "method": request.method
            }
        }
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_data
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, 
        exc: RequestValidationError
    ) -> JSONResponse:
        """Handle request validation errors."""
        logger.warning(
            f"Validation error: {exc.errors()} - "
            f"Path: {request.url.path} - Method: {request.method}"
        )
        
        error_data = {
            "success": False,
            "message": "Validation error in request data",
            "error_code": "VALIDATION_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "validation_errors": exc.errors(),
                "path": str(request.url.path),
                "method": request.method
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_data
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Handle ValueError exceptions."""
        logger.error(
            f"Value error: {str(exc)} - "
            f"Path: {request.url.path} - Method: {request.method}"
        )
        
        error_data = {
            "success": False,
            "message": "Invalid value provided",
            "error_code": "VALUE_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "error_message": str(exc),
                "path": str(request.url.path),
                "method": request.method
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_data
        )
    
    @app.exception_handler(FileNotFoundError)
    async def file_not_found_error_handler(
        request: Request, 
        exc: FileNotFoundError
    ) -> JSONResponse:
        """Handle FileNotFoundError exceptions."""
        logger.error(
            f"File not found: {str(exc)} - "
            f"Path: {request.url.path} - Method: {request.method}"
        )
        
        error_data = {
            "success": False,
            "message": "Requested file not found",
            "error_code": "FILE_NOT_FOUND",
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "error_message": str(exc),
                "path": str(request.url.path),
                "method": request.method
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_data
        )
    
    @app.exception_handler(PermissionError)
    async def permission_error_handler(
        request: Request, 
        exc: PermissionError
    ) -> JSONResponse:
        """Handle PermissionError exceptions."""
        logger.error(
            f"Permission error: {str(exc)} - "
            f"Path: {request.url.path} - Method: {request.method}"
        )
        
        error_data = {
            "success": False,
            "message": "Permission denied",
            "error_code": "PERMISSION_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "error_message": str(exc),
                "path": str(request.url.path),
                "method": request.method
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=error_data
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all other exceptions."""
        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {str(exc)} - "
            f"Path: {request.url.path} - Method: {request.method}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        
        error_data = {
            "success": False,
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "error_type": type(exc).__name__,
                "path": str(request.url.path),
                "method": request.method
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_data
        )


class APIException(HTTPException):
    """Custom API exception with additional context."""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str = None,
        details: dict = None
    ):
        self.error_code = error_code or f"HTTP_{status_code}"
        self.details = details or {}
        super().__init__(status_code=status_code, detail=message)


class VideoProcessingException(APIException):
    """Exception for video processing errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="VIDEO_PROCESSING_ERROR",
            details=details
        )


class ModelException(APIException):
    """Exception for ML model errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=message,
            error_code="MODEL_ERROR",
            details=details
        )


class ResourceNotFoundException(APIException):
    """Exception for resource not found errors."""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"{resource_type} with ID '{resource_id}' not found",
            error_code="RESOURCE_NOT_FOUND",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )