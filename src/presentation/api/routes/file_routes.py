from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import os
from pathlib import Path

from src.infrastructure.config.dependencies import DependencyContainer
from src.infrastructure.config.settings import Settings
from src.presentation.api.models.request_models import (
    ValidateVideoRequest,
    CopyVideoRequest,
    MoveVideoRequest,
    DiscoverVideosRequest,
    ListFilesRequest,
    CleanupRequest
)
from src.presentation.api.models.response_models import (
    FileValidationResponse,
    ApiResponse,
    DiskUsageResponse,
    BackupResponse,
    CleanupResponse,
    FileListResponse
)
from src.presentation.api.middleware.error_handler import (
    VideoProcessingException,
    ResourceNotFoundException
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


@router.post("/validate", response_model=FileValidationResponse)
async def validate_video_file(
    request: ValidateVideoRequest,
    container: DependencyContainer = Depends(get_dependency_container)
) -> FileValidationResponse:
    """Validate a video file for processing."""
    try:
        logger.info(f"Validating video file: {request.file_path}")
        
        # Get file management service
        file_service = container.get_file_management_app_service()
        
        # Validate file
        validation_result = await file_service.validate_video_file(
            file_path=request.file_path,
            check_format=request.check_format,
            check_size=request.check_size,
            check_corruption=request.check_corruption
        )
        
        return FileValidationResponse(
            success=True,
            message="Video file validation completed",
            data={
                "file_path": request.file_path,
                "is_valid": validation_result['is_valid'],
                "validation_details": validation_result['details'],
                "file_info": validation_result.get('file_info', {}),
                "errors": validation_result.get('errors', []),
                "warnings": validation_result.get('warnings', [])
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to validate video file: {e}")
        if isinstance(e, (VideoProcessingException, HTTPException)):
            raise
        raise VideoProcessingException(
            f"Failed to validate video file: {str(e)}",
            {"file_path": request.file_path}
        )


@router.post("/copy", response_model=ApiResponse)
async def copy_video_file(
    request: CopyVideoRequest,
    container: DependencyContainer = Depends(get_dependency_container)
) -> ApiResponse:
    """Copy a video file to the workspace."""
    try:
        logger.info(f"Copying video file from {request.source_path} to {request.destination_path}")
        
        # Get file management service
        file_service = container.get_file_management_app_service()
        
        # Copy file
        copy_result = await file_service.copy_video_to_workspace(
            source_path=request.source_path,
            destination_path=request.destination_path,
            overwrite=request.overwrite
        )
        
        return ApiResponse(
            success=True,
            message="Video file copied successfully",
            data={
                "source_path": request.source_path,
                "destination_path": copy_result['destination_path'],
                "file_size_bytes": copy_result['file_size_bytes'],
                "copy_time_seconds": copy_result['copy_time_seconds'],
                "overwritten": copy_result.get('overwritten', False)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to copy video file: {e}")
        if isinstance(e, (VideoProcessingException, HTTPException)):
            raise
        raise VideoProcessingException(
            f"Failed to copy video file: {str(e)}",
            {
                "source_path": request.source_path,
                "destination_path": request.destination_path
            }
        )


@router.post("/move", response_model=ApiResponse)
async def move_video_file(
    request: MoveVideoRequest,
    container: DependencyContainer = Depends(get_dependency_container)
) -> ApiResponse:
    """Move a video file to the workspace."""
    try:
        logger.info(f"Moving video file from {request.source_path} to {request.destination_path}")
        
        # Get file management service
        file_service = container.get_file_management_app_service()
        
        # Move file
        move_result = await file_service.move_video_to_workspace(
            source_path=request.source_path,
            destination_path=request.destination_path,
            overwrite=request.overwrite
        )
        
        return ApiResponse(
            success=True,
            message="Video file moved successfully",
            data={
                "source_path": request.source_path,
                "destination_path": move_result['destination_path'],
                "file_size_bytes": move_result['file_size_bytes'],
                "move_time_seconds": move_result['move_time_seconds'],
                "overwritten": move_result.get('overwritten', False)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to move video file: {e}")
        if isinstance(e, (VideoProcessingException, HTTPException)):
            raise
        raise VideoProcessingException(
            f"Failed to move video file: {str(e)}",
            {
                "source_path": request.source_path,
                "destination_path": request.destination_path
            }
        )


@router.post("/discover", response_model=ApiResponse)
async def discover_videos(
    request: DiscoverVideosRequest,
    container: DependencyContainer = Depends(get_dependency_container)
) -> ApiResponse:
    """Discover video files in a directory."""
    try:
        logger.info(f"Discovering videos in directory: {request.directory_path}")
        
        # Get file management service
        file_service = container.get_file_management_app_service()
        
        # Discover videos
        discovery_result = await file_service.discover_videos_in_directory(
            directory_path=request.directory_path,
            recursive=request.recursive,
            include_subdirs=request.include_subdirs,
            file_extensions=request.file_extensions
        )
        
        return ApiResponse(
            success=True,
            message=f"Discovered {len(discovery_result['videos'])} video files",
            data={
                "directory_path": request.directory_path,
                "videos_found": len(discovery_result['videos']),
                "videos": discovery_result['videos'],
                "total_size_bytes": discovery_result['total_size_bytes'],
                "total_size_mb": round(discovery_result['total_size_bytes'] / (1024**2), 2),
                "discovery_time_seconds": discovery_result['discovery_time_seconds'],
                "subdirectories_scanned": discovery_result.get('subdirectories_scanned', 0)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to discover videos: {e}")
        if isinstance(e, (VideoProcessingException, HTTPException)):
            raise
        raise VideoProcessingException(
            f"Failed to discover videos: {str(e)}",
            {"directory_path": request.directory_path}
        )


@router.get("/list", response_model=FileListResponse)
async def list_files(
    directory_path: str = Query(..., description="Directory path to list files from"),
    file_type: Optional[str] = Query(None, description="Filter by file type (video, image, etc.)"),
    include_hidden: bool = Query(False, description="Include hidden files"),
    recursive: bool = Query(False, description="List files recursively"),
    container: DependencyContainer = Depends(get_dependency_container)
) -> FileListResponse:
    """List files in a directory with detailed information."""
    try:
        logger.info(f"Listing files in directory: {directory_path}")
        
        # Get file management service
        file_service = container.get_file_management_app_service()
        
        # List files
        file_list = await file_service.list_files_in_directory(
            directory_path=directory_path,
            file_type=file_type,
            include_hidden=include_hidden,
            recursive=recursive
        )
        
        return FileListResponse(
            success=True,
            message=f"Listed {len(file_list['files'])} files",
            data={
                "directory_path": directory_path,
                "files_count": len(file_list['files']),
                "files": file_list['files'],
                "total_size_bytes": file_list['total_size_bytes'],
                "total_size_mb": round(file_list['total_size_bytes'] / (1024**2), 2),
                "filters": {
                    "file_type": file_type,
                    "include_hidden": include_hidden,
                    "recursive": recursive
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        if isinstance(e, (VideoProcessingException, HTTPException)):
            raise
        raise VideoProcessingException(
            f"Failed to list files: {str(e)}",
            {"directory_path": directory_path}
        )


@router.get("/disk-usage", response_model=DiskUsageResponse)
async def get_disk_usage(
    container: DependencyContainer = Depends(get_dependency_container),
    settings: Settings = Depends(get_settings)
) -> DiskUsageResponse:
    """Get disk usage information for application directories."""
    try:
        # Get file management service
        file_service = container.get_file_management_app_service()
        
        # Get disk usage
        disk_usage = await file_service.get_disk_usage_info()
        
        return DiskUsageResponse(
            success=True,
            message="Disk usage information retrieved",
            data=disk_usage
        )
        
    except Exception as e:
        logger.error(f"Failed to get disk usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get disk usage information"
        )


@router.post("/backup", response_model=BackupResponse)
async def create_backup(
    include_results: bool = Query(True, description="Include detection results in backup"),
    include_config: bool = Query(True, description="Include configuration in backup"),
    include_logs: bool = Query(False, description="Include logs in backup"),
    backup_path: Optional[str] = Query(None, description="Custom backup path"),
    container: DependencyContainer = Depends(get_dependency_container)
) -> BackupResponse:
    """Create a backup of application data."""
    try:
        logger.info("Creating application backup")
        
        # Get file management service
        file_service = container.get_file_management_app_service()
        
        # Create backup
        backup_result = await file_service.create_backup(
            include_results=include_results,
            include_config=include_config,
            include_logs=include_logs,
            backup_path=backup_path
        )
        
        return BackupResponse(
            success=True,
            message="Backup created successfully",
            data={
                "backup_path": backup_result['backup_path'],
                "backup_size_bytes": backup_result['backup_size_bytes'],
                "backup_size_mb": round(backup_result['backup_size_bytes'] / (1024**2), 2),
                "files_included": backup_result['files_included'],
                "backup_time_seconds": backup_result['backup_time_seconds'],
                "includes": {
                    "results": include_results,
                    "config": include_config,
                    "logs": include_logs
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create backup"
        )


@router.post("/cleanup", response_model=CleanupResponse)
async def cleanup_files(
    request: CleanupRequest,
    container: DependencyContainer = Depends(get_dependency_container)
) -> CleanupResponse:
    """Clean up old files and temporary data."""
    try:
        logger.info(f"Cleaning up files older than {request.older_than_days} days")
        
        # Get file management service
        file_service = container.get_file_management_app_service()
        
        # Perform cleanup
        cleanup_result = await file_service.cleanup_old_files(
            older_than_days=request.older_than_days,
            include_output=request.include_output,
            include_logs=request.include_logs,
            include_temp=request.include_temp,
            dry_run=request.dry_run
        )
        
        return CleanupResponse(
            success=True,
            message=f"Cleanup completed - {'Dry run: ' if request.dry_run else ''}removed {cleanup_result['files_removed']} files",
            data={
                "files_removed": cleanup_result['files_removed'],
                "space_freed_bytes": cleanup_result['space_freed_bytes'],
                "space_freed_mb": round(cleanup_result['space_freed_bytes'] / (1024**2), 2),
                "cleanup_time_seconds": cleanup_result['cleanup_time_seconds'],
                "dry_run": request.dry_run,
                "criteria": {
                    "older_than_days": request.older_than_days,
                    "include_output": request.include_output,
                    "include_logs": request.include_logs,
                    "include_temp": request.include_temp
                },
                "removed_files": cleanup_result.get('removed_files', [])
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to cleanup files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup files"
        )


@router.delete("/", response_model=ApiResponse)
async def delete_file(
    file_path: str = Query(..., description="Path to file to delete"),
    force: bool = Query(False, description="Force delete without confirmation"),
    container: DependencyContainer = Depends(get_dependency_container)
) -> ApiResponse:
    """Delete a specific file."""
    try:
        logger.info(f"Deleting file: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise ResourceNotFoundException("file", file_path)
        
        # Get file info before deletion
        file_stat = os.stat(file_path)
        file_size = file_stat.st_size
        
        # Delete file
        os.remove(file_path)
        
        return ApiResponse(
            success=True,
            message="File deleted successfully",
            data={
                "file_path": file_path,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024**2), 2),
                "force_delete": force
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to delete file {file_path}: {e}")
        if isinstance(e, (ResourceNotFoundException, HTTPException)):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )


@router.get("/info/{file_path:path}", response_model=ApiResponse)
async def get_file_info(
    file_path: str,
    container: DependencyContainer = Depends(get_dependency_container)
) -> ApiResponse:
    """Get detailed information about a file."""
    try:
        logger.info(f"Getting file info: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise ResourceNotFoundException("file", file_path)
        
        # Get file management service
        file_service = container.get_file_management_app_service()
        
        # Get file info
        file_info = await file_service.get_file_info(file_path)
        
        return ApiResponse(
            success=True,
            message="File information retrieved",
            data=file_info
        )
        
    except Exception as e:
        logger.error(f"Failed to get file info for {file_path}: {e}")
        if isinstance(e, (ResourceNotFoundException, HTTPException)):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file information"
        )