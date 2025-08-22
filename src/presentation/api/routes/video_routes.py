from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File, Form
from typing import List, Optional
import os
from pathlib import Path

from src.infrastructure.config.dependencies import DependencyContainer
from src.infrastructure.config.settings import Settings
from src.presentation.api.models.request_models import (
    ProcessVideoRequest,
    ProcessMultipleVideosRequest,
    UpdateConfidenceRequest,
    PaginationRequest
)
from src.presentation.api.models.response_models import (
    ProcessVideoResponse,
    VideoResponse,
    VideoListResponse,
    ProcessingStatusResponse,
    DetectionResultResponse,
    ApiResponse,
    BoundingBoxResponse,
    DamageResponse,
    DetectionStatisticsResponse,
    VideoMetadataResponse
)
from src.presentation.api.middleware.error_handler import (
    VideoProcessingException,
    ResourceNotFoundException
)
from src.infrastructure.config.logging_config import get_logger
from src.domain.entities.video import VideoStatus

logger = get_logger(__name__)
router = APIRouter()


def get_dependency_container() -> DependencyContainer:
    """Get dependency container instance."""
    return DependencyContainer()


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()


@router.post("/process", response_model=ProcessVideoResponse)
async def process_video(
    request: ProcessVideoRequest,
    background_tasks: BackgroundTasks,
    container: DependencyContainer = Depends(get_dependency_container)
) -> ProcessVideoResponse:
    """Process a single video for damage detection."""
    try:
        logger.info(f"Processing video request: {request.video_path}")
        
        # Get video processing service and settings
        video_app_service = container.get_video_processing_app_service()
        settings = container.get_settings()
        
        # Construct full video path
        from pathlib import Path
        video_path = settings.videos_dir / request.video_path
        
        # Validate video file exists
        if not video_path.exists():
            raise VideoProcessingException(
                f"Video file not found: {request.video_path}",
                {"video_path": request.video_path}
            )
        
        # Execute video processing
        detection_result = await video_app_service.process_single_video(
            video_path=video_path
        )
        
        task_id = detection_result.id
        
        # Convert DetectionResult to DetectionResultResponse
        detection_response = DetectionResultResponse(
            id=detection_result.id,
            video_id=detection_result.video.id,
            damages=[
                DamageResponse(
                    damage_type=damage.damage_type,
                    severity=damage.severity,
                    confidence=damage.confidence,
                    bounding_box=BoundingBoxResponse(
                        x=damage.bounding_box.x,
                        y=damage.bounding_box.y,
                        width=damage.bounding_box.width,
                        height=damage.bounding_box.height
                    ),
                    frame_number=damage.frame_number,
                    timestamp=damage.timestamp
                ) for damage in detection_result.damages
            ],
            statistics=DetectionStatisticsResponse(
                total_frames_processed=detection_result.statistics.total_frames_processed,
                frames_with_damage=len([d for d in detection_result.damages]),
                total_damages_detected=detection_result.statistics.total_damages_detected,
                processing_time_seconds=detection_result.statistics.processing_time,
                average_confidence=detection_result.statistics.average_confidence
            ),
            video_metadata=VideoMetadataResponse(
                file_path=str(detection_result.video.file_path),
                duration_seconds=detection_result.video.metadata.duration,
                fps=detection_result.video.metadata.fps,
                width=detection_result.video.metadata.width,
                height=detection_result.video.metadata.height,
                format=detection_result.video.metadata.format,
                file_size_mb=detection_result.video.metadata.file_size / (1024 * 1024)
            ) if detection_result.video.metadata else None,
            model_version=detection_result.model_version,
            confidence_threshold=detection_result.confidence_threshold,
            created_at=detection_result.created_at,
            annotated_video_path=str(detection_result.annotated_video_path) if detection_result.annotated_video_path else None
        )
        
        return ProcessVideoResponse(
            success=True,
            message="Video processing completed successfully",
            video_id=detection_result.video.id,
            detection_result=detection_response
        )
        
    except Exception as e:
        logger.error(f"Failed to process video: {e}")
        if isinstance(e, (VideoProcessingException, HTTPException)):
            raise
        raise VideoProcessingException(
            f"Failed to start video processing: {str(e)}",
            {"video_path": request.video_path}
        )


@router.post("/process-multiple", response_model=ApiResponse)
async def process_multiple_videos(
    request: ProcessMultipleVideosRequest,
    background_tasks: BackgroundTasks,
    container: DependencyContainer = Depends(get_dependency_container)
) -> ApiResponse:
    """Process multiple videos for damage detection."""
    try:
        logger.info(f"Processing multiple videos: {len(request.video_paths)} videos")
        
        # Get video processing service
        video_app_service = container.get_video_processing_app_service()
        
        # Validate all video files exist
        missing_files = []
        for video_path in request.video_paths:
            if not os.path.exists(video_path):
                missing_files.append(video_path)
        
        if missing_files:
            raise VideoProcessingException(
                f"Video files not found: {missing_files}",
                {"missing_files": missing_files}
            )
        
        # Start batch processing
        task_ids = await video_app_service.process_multiple_videos_async(
            video_paths=request.video_paths,
            confidence_threshold=request.confidence_threshold,
            create_annotated_video=request.create_annotated_video,
            create_thumbnail=request.create_thumbnail,
            max_concurrent=request.max_concurrent
        )
        
        return ApiResponse(
            success=True,
            message=f"Started processing {len(request.video_paths)} videos",
            data={
                "task_ids": task_ids,
                "video_count": len(request.video_paths),
                "max_concurrent": request.max_concurrent,
                "confidence_threshold": request.confidence_threshold
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to process multiple videos: {e}")
        if isinstance(e, (VideoProcessingException, HTTPException)):
            raise
        raise VideoProcessingException(
            f"Failed to start batch video processing: {str(e)}",
            {"video_count": len(request.video_paths)}
        )


@router.post("/upload", response_model=ApiResponse)
async def upload_and_process_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    confidence_threshold: Optional[float] = Form(0.5),
    create_annotated_video: Optional[bool] = Form(True),
    create_thumbnail: Optional[bool] = Form(True),
    container: DependencyContainer = Depends(get_dependency_container),
    settings: Settings = Depends(get_settings)
) -> ProcessVideoResponse:
    """Upload and process a video file."""
    try:
        logger.info(f"Uploading and processing video: {file.filename}")
        
        # Validate file type
        if not file.filename:
            raise VideoProcessingException("No filename provided")
        
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.supported_formats:
            raise VideoProcessingException(
                f"Unsupported video format: {file_extension}",
                {
                    "provided_format": file_extension,
                    "supported_formats": settings.supported_formats
                }
            )
        
        # Check file size
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        max_size_bytes = settings.max_video_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            raise VideoProcessingException(
                f"File too large: {file_size / (1024*1024):.1f}MB (max: {settings.max_video_size_mb}MB)",
                {
                    "file_size_mb": file_size / (1024*1024),
                    "max_size_mb": settings.max_video_size_mb
                }
            )
        
        # Save uploaded file
        upload_path = os.path.join(settings.videos_dir, file.filename)
        os.makedirs(settings.videos_dir, exist_ok=True)
        
        with open(upload_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved uploaded video to: {upload_path}")
        
        # Get video processing service
        video_app_service = container.get_video_processing_app_service()
        
        # Start processing
        detection_result = await video_app_service.process_single_video(
            video_path=Path(upload_path)
        )
        
        task_id = detection_result.id
        
        return ApiResponse(
            success=True,
            message="Video uploaded and processing started",
            data={
                "task_id": task_id,
                "video_path": upload_path,
                "filename": file.filename,
                "file_size_mb": round(file_size / (1024*1024), 2),
                "status": "processing",
                "confidence_threshold": confidence_threshold
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to upload and process video: {e}")
        if isinstance(e, (VideoProcessingException, HTTPException)):
            raise
        raise VideoProcessingException(
            f"Failed to upload and process video: {str(e)}",
            {"filename": file.filename if file.filename else "unknown"}
        )


@router.get("/status/{task_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(
    task_id: str,
    container: DependencyContainer = Depends(get_dependency_container)
) -> ProcessingStatusResponse:
    """Get the processing status of a video."""
    try:
        # Get video processing service
        video_app_service = container.get_video_processing_app_service()
        
        # Get status
        status_info = await video_app_service.get_processing_status(task_id)
        
        if not status_info:
            raise ResourceNotFoundException("processing_task", task_id)
        
        return ProcessingStatusResponse(
            success=True,
            message="Processing status retrieved",
            data=status_info
        )
        
    except Exception as e:
        logger.error(f"Failed to get processing status: {e}")
        if isinstance(e, (ResourceNotFoundException, HTTPException)):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get processing status"
        )


@router.get("/", response_model=VideoListResponse)
async def list_videos(
    pagination: PaginationRequest = Depends(),
    status_filter: Optional[VideoStatus] = None,
    container: DependencyContainer = Depends(get_dependency_container)
) -> VideoListResponse:
    """List videos with optional filtering and pagination."""
    try:
        # Get video repository
        video_repo = container.get_video_repository()
        
        # Get videos based on status filter
        if status_filter:
            videos = await video_repo.find_by_status(status_filter)
        else:
            videos = await video_repo.find_all()
        
        # Apply pagination
        total_count = len(videos)
        start_idx = (pagination.page - 1) * pagination.page_size
        end_idx = start_idx + pagination.page_size
        paginated_videos = videos[start_idx:end_idx]
        
        # Convert to response format
        video_responses = [
            VideoResponse(
                id=video.id,
                file_path=str(video.file_path),
                status=video.status,
                created_at=video.created_at,
                updated_at=video.updated_at,
                metadata=VideoMetadataResponse(
                    file_path=str(video.file_path),
                    duration_seconds=video.metadata.duration,
                    fps=video.metadata.fps,
                    width=video.metadata.width,
                    height=video.metadata.height,
                    format=video.metadata.format,
                    file_size_mb=video.metadata.file_size / (1024 * 1024)
                ) if video.metadata else None
            ) for video in paginated_videos
        ]
        
        return VideoListResponse(
            success=True,
            message=f"Retrieved {len(video_responses)} videos",
            videos=video_responses,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"Failed to list videos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list videos"
        )


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: str,
    container: DependencyContainer = Depends(get_dependency_container)
) -> VideoResponse:
    """Get a specific video by ID."""
    try:
        # Get video repository
        video_repo = container.get_video_repository()
        
        # Find video
        video = await video_repo.find_by_id(video_id)
        if not video:
            raise ResourceNotFoundException("video", video_id)
        
        video_response = VideoResponse(
            id=video.id,
            file_path=str(video.file_path),
            status=video.status,
            created_at=video.created_at,
            updated_at=video.updated_at,
            metadata=VideoMetadataResponse(
                file_path=str(video.file_path),
                duration_seconds=video.metadata.duration,
                fps=video.metadata.fps,
                width=video.metadata.width,
                height=video.metadata.height,
                format=video.metadata.format,
                file_size_mb=video.metadata.file_size / (1024 * 1024)
            ) if video.metadata else None
        )
        
        return video_response
        
    except Exception as e:
        logger.error(f"Failed to get video {video_id}: {e}")
        if isinstance(e, (ResourceNotFoundException, HTTPException)):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get video"
        )


@router.put("/confidence", response_model=ApiResponse)
async def update_confidence_threshold(
    request: UpdateConfidenceRequest,
    container: DependencyContainer = Depends(get_dependency_container)
) -> ApiResponse:
    """Update the confidence threshold for damage detection."""
    try:
        # Get damage detection service
        detection_service = container.get_damage_detection_service()
        
        # Update confidence threshold
        detection_service.set_confidence_threshold(request.confidence_threshold)
        
        return ApiResponse(
            success=True,
            message="Confidence threshold updated",
            data={
                "confidence_threshold": request.confidence_threshold,
                "previous_threshold": detection_service.get_confidence_threshold()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to update confidence threshold: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update confidence threshold"
        )


@router.delete("/{video_id}", response_model=ApiResponse)
async def delete_video(
    video_id: str,
    delete_files: bool = False,
    container: DependencyContainer = Depends(get_dependency_container)
) -> ApiResponse:
    """Delete a video and optionally its associated files."""
    try:
        # Get repositories
        video_repo = container.get_video_repository()
        detection_repo = container.get_detection_repository()
        
        # Find video
        video = video_repo.find_by_id(video_id)
        if not video:
            raise ResourceNotFoundException("video", video_id)
        
        # Delete associated detection results
        detection_results = detection_repo.find_by_video_id(video_id)
        for result in detection_results:
            detection_repo.delete(result.id)
        
        # Delete files if requested
        deleted_files = []
        if delete_files:
            # Delete video file
            if os.path.exists(video.file_path):
                os.remove(video.file_path)
                deleted_files.append(video.file_path)
            
            # Delete output files (annotated video, thumbnail, etc.)
            # This would need to be implemented based on your file naming convention
        
        # Delete video record
        video_repo.delete(video_id)
        
        return ApiResponse(
            success=True,
            message="Video deleted successfully",
            data={
                "video_id": video_id,
                "deleted_detection_results": len(detection_results),
                "deleted_files": deleted_files
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to delete video {video_id}: {e}")
        if isinstance(e, (ResourceNotFoundException, HTTPException)):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete video"
        )