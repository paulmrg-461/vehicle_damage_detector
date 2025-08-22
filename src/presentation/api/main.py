from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Any
import uvicorn

from src.infrastructure.config.settings import Settings
from src.infrastructure.config.logging_config import setup_logging, get_logger
from src.infrastructure.config.dependencies import DependencyContainer
from src.presentation.api.routes import (
    video_routes,
    detection_routes,
    file_routes,
    health_routes
)
from src.presentation.api.middleware.error_handler import add_error_handlers
from src.presentation.api.middleware.logging_middleware import LoggingMiddleware

# Initialize settings and logging
settings = Settings()
setup_logging()
logger = get_logger(__name__)

# Initialize dependency container
dependency_container = DependencyContainer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Vehicle Damage Detection API")
    
    # Initialize dependencies
    try:
        health_status = await dependency_container.health_check()
        if not all(health_status.values()):
            logger.warning(f"Some dependencies failed health check: {health_status}")
        else:
            logger.info("All dependencies initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize dependencies: {e}")
        raise
    
    yield
    
    logger.info("Shutting down Vehicle Damage Detection API")


# Create FastAPI application
app = FastAPI(
    title="Vehicle Damage Detection API",
    description="API for detecting and analyzing vehicle damage using AI/ML models",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(LoggingMiddleware)

# Add error handlers
add_error_handlers(app)

# Include routers
app.include_router(
    health_routes.router,
    prefix="/api/v1/health",
    tags=["Health"]
)

app.include_router(
    video_routes.router,
    prefix="/api/v1/videos",
    tags=["Videos"]
)

app.include_router(
    detection_routes.router,
    prefix="/api/v1/detections",
    tags=["Detections"]
)

app.include_router(
    file_routes.router,
    prefix="/api/v1/files",
    tags=["Files"]
)


@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Vehicle Damage Detection API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health"
    }


@app.get("/api/v1/info", response_model=Dict[str, Any])
async def api_info():
    """Get API information and configuration."""
    return {
        "api_name": "Vehicle Damage Detection API",
        "version": "1.0.0",
        "environment": settings.environment,
        "debug": settings.debug,
        "supported_formats": settings.supported_video_formats,
        "max_file_size_mb": settings.max_file_size_mb,
        "model_info": {
            "name": settings.yolo_model_name,
            "confidence_threshold": settings.yolo_confidence_threshold,
            "iou_threshold": settings.yolo_iou_threshold
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.presentation.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )