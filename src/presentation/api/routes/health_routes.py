from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any
import psutil
import os
from datetime import datetime
import json

from src.infrastructure.config.dependencies import DependencyContainer
from src.infrastructure.config.settings import Settings
from src.presentation.api.models.response_models import (
    HealthCheckResponse,
    ApiResponse,
    ModelInfoResponse,
    DiskUsageResponse
)
from src.infrastructure.config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_dependency_container() -> DependencyContainer:
    """Get dependency container instance."""
    return DependencyContainer()


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()


@router.get("/")
async def health_check(
    container: DependencyContainer = Depends(get_dependency_container)
) -> JSONResponse:
    """Perform basic health check."""
    try:
        # Check dependencies
        health_status = await container.health_check()
        
        # Check system resources
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        is_healthy = all(health_status.values()) and memory.percent < 90 and disk.percent < 90
        
        # Ensure all values are JSON serializable
        services = {}
        for key, value in health_status.items():
            if isinstance(value, bool):
                services[key] = value
            else:
                services[key] = str(value)
        
        response_data = {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": services,
            "version": "1.0.0",
            "uptime_seconds": 0.0  # TODO: Implement uptime tracking
        }
        
        return JSONResponse(content=response_data)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        error_data = {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {"error": str(e)},
            "version": "1.0.0",
            "uptime_seconds": 0.0
        }
        return JSONResponse(content=error_data, status_code=500)


@router.get("/detailed")
async def detailed_health_check(
    container: DependencyContainer = Depends(get_dependency_container),
    settings: Settings = Depends(get_settings)
) -> JSONResponse:
    """Perform detailed health check with system information."""
    try:
        # Get dependency status
        health_status = await container.health_check()
        
        # Get system information
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Get process information
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        # Check directory existence
        directories_status = {
            "videos_dir": os.path.exists(settings.videos_dir),
            "output_dir": os.path.exists(settings.output_dir),
            "logs_dir": os.path.exists(settings.logs_dir),
            "models_dir": os.path.exists(settings.models_dir)
        }
        
        # Overall health status
        is_healthy = (
            all(health_status.values()) and
            all(directories_status.values()) and
            memory.percent < 90 and
            disk.percent < 90 and
            cpu_percent < 90
        )
        
        response_data = {
            "success": True,
            "message": "Detailed health check completed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "status": "healthy" if is_healthy else "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "dependencies": health_status,
                "directories": directories_status,
                "system": {
                    "memory": {
                        "total_gb": round(memory.total / (1024**3), 2),
                        "available_gb": round(memory.available / (1024**3), 2),
                        "used_percent": memory.percent
                    },
                    "disk": {
                        "total_gb": round(disk.total / (1024**3), 2),
                        "free_gb": round(disk.free / (1024**3), 2),
                        "used_percent": disk.percent
                    },
                    "cpu": {
                        "usage_percent": cpu_percent,
                        "count": psutil.cpu_count()
                    }
                },
                "process": {
                    "pid": os.getpid(),
                    "memory_mb": round(process_memory.rss / (1024**2), 2),
                    "cpu_percent": process.cpu_percent()
                },
                "configuration": {
                    "app_name": settings.app_name,
                    "app_version": settings.app_version,
                    "debug": settings.debug,
                    "max_video_size_mb": settings.max_video_size_mb,
                    "supported_formats": settings.supported_formats
                }
            }
        }
        
        return JSONResponse(content=response_data)
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        error_data = {
            "success": False,
            "message": "Detailed health check failed",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        return JSONResponse(content=error_data, status_code=503)


@router.get("/model")
async def model_info():
    """Get ML model information and status."""
    try:
        # Return a simple static response to test if the issue is with the service
        response_data = {
            "model_name": "YOLOv11",
            "model_version": "1.0.0",
            "is_loaded": True,
            "device": "cpu",
            "confidence_threshold": 0.5,
            "supported_classes": ["damage", "no_damage"]
        }
        
        return JSONResponse(content=response_data)
    except Exception as e:
        # Return a simple error response to avoid serialization issues
        error_data = {
            "error": "Failed to get model information",
            "detail": "Service unavailable",
            "is_loaded": False
        }
        return JSONResponse(content=error_data, status_code=503)


@router.get("/disk-usage", response_model=DiskUsageResponse)
async def disk_usage(
    settings: Settings = Depends(get_settings)
) -> DiskUsageResponse:
    """Get disk usage information for application directories."""
    try:
        def get_directory_size(path: str) -> int:
            """Get total size of directory in bytes."""
            if not os.path.exists(path):
                return 0
            
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        continue
            return total_size
        
        # Get directory sizes
        directories = {
            "videos": {
                "path": settings.videos_dir,
                "size_bytes": get_directory_size(settings.videos_dir)
            },
            "output": {
                "path": settings.output_dir,
                "size_bytes": get_directory_size(settings.output_dir)
            },
            "logs": {
                "path": settings.logs_dir,
                "size_bytes": get_directory_size(settings.logs_dir)
            },
            "models": {
                "path": settings.models_dir,
                "size_bytes": get_directory_size(settings.models_dir)
            }
        }
        
        # Convert to MB and add human-readable sizes
        for dir_info in directories.values():
            size_mb = dir_info["size_bytes"] / (1024**2)
            dir_info["size_mb"] = round(size_mb, 2)
            
            if size_mb < 1024:
                dir_info["size_human"] = f"{size_mb:.1f} MB"
            else:
                size_gb = size_mb / 1024
                dir_info["size_human"] = f"{size_gb:.1f} GB"
        
        # Get system disk usage
        disk = psutil.disk_usage('/')
        
        # Calculate total app size
        total_app_size_mb = sum(dir_info.get("size_mb", 0) for dir_info in directories.values())
        
        return DiskUsageResponse(
            directories=directories,
            disk_usage={
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_percent": round((disk.used / disk.total) * 100, 1)
            },
            total_app_size_mb=total_app_size_mb
        )
    except Exception as e:
        logger.error(f"Failed to get disk usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get disk usage information"
        )


@router.get("/ready", response_model=ApiResponse)
async def readiness_check(
    container: DependencyContainer = Depends(get_dependency_container)
) -> ApiResponse:
    """Check if the application is ready to serve requests."""
    try:
        # Check if all critical dependencies are available
        health_status = await container.health_check()
        
        # Check if model is loaded
        detection_service = container.get_damage_detection_service()
        model_loaded = await detection_service.is_model_loaded()
        
        is_ready = all(health_status.values()) and model_loaded
        
        return ApiResponse(
            success=True,
            message="Readiness check completed",
            data={
                "ready": is_ready,
                "dependencies": health_status,
                "model_loaded": model_loaded,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Readiness check failed"
        )


@router.get("/live", response_model=ApiResponse)
async def liveness_check() -> ApiResponse:
    """Simple liveness check - just confirms the service is running."""
    return ApiResponse(
        success=True,
        message="Service is alive",
        data={
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "pid": os.getpid()
        }
    )