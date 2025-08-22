from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, date

from src.infrastructure.config.dependencies import DependencyContainer
from src.presentation.api.models.request_models import (
    GetDetectionResultsRequest,
    SearchResultsRequest,
    GetTrendsRequest,
    ExportResultsRequest,
    PaginationRequest
)
from src.presentation.api.models.response_models import (
    DetectionResultResponse,
    DetectionResultListResponse,
    StatisticsResponse,
    SearchResultsResponse,
    TrendsResponse,
    ApiResponse
)
from src.presentation.api.middleware.error_handler import ResourceNotFoundException
from src.infrastructure.config.logging_config import get_logger
from src.domain.entities.damage import DamageType, DamageSeverity

logger = get_logger(__name__)
router = APIRouter()


def get_dependency_container() -> DependencyContainer:
    """Get dependency container instance."""
    return DependencyContainer()


@router.get("/", response_model=DetectionResultListResponse)
async def get_detection_results(
    pagination: PaginationRequest = Depends(),
    video_id: Optional[str] = Query(None, description="Filter by video ID"),
    damage_type: Optional[DamageType] = Query(None, description="Filter by damage type"),
    severity: Optional[DamageSeverity] = Query(None, description="Filter by damage severity"),
    start_date: Optional[date] = Query(None, description="Filter results from this date"),
    end_date: Optional[date] = Query(None, description="Filter results until this date"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    container: DependencyContainer = Depends(get_dependency_container)
) -> DetectionResultListResponse:
    """Get detection results with optional filtering and pagination."""
    try:
        logger.info(f"Getting detection results with filters: video_id={video_id}, damage_type={damage_type}")
        
        # Get detection results service
        detection_app_service = container.get_detection_results_app_service()
        
        # Build filter parameters
        filters = {}
        if video_id:
            filters['video_id'] = video_id
        if damage_type:
            filters['damage_type'] = damage_type
        if severity:
            filters['severity'] = severity
        if start_date:
            filters['start_date'] = datetime.combine(start_date, datetime.min.time())
        if end_date:
            filters['end_date'] = datetime.combine(end_date, datetime.max.time())
        if min_confidence:
            filters['min_confidence'] = min_confidence
        
        # Get results
        results = await detection_app_service.get_detection_results_filtered(
            filters=filters,
            page=pagination.page,
            page_size=pagination.page_size
        )
        
        # Convert to response format
        detection_responses = []
        for result in results['results']:
            detection_responses.append({
                "id": result.id,
                "video_id": result.video_id,
                "damages": [
                    {
                        "id": damage.id,
                        "type": damage.type,
                        "severity": damage.severity,
                        "confidence": damage.confidence,
                        "bounding_box": {
                            "x": damage.bounding_box.x,
                            "y": damage.bounding_box.y,
                            "width": damage.bounding_box.width,
                            "height": damage.bounding_box.height
                        },
                        "frame_number": damage.frame_number,
                        "timestamp": damage.timestamp,
                        "area_pixels": damage.area_pixels,
                        "description": damage.description
                    } for damage in result.damages
                ],
                "statistics": {
                    "total_frames_processed": result.statistics.total_frames_processed,
                    "damages_detected": result.statistics.damages_detected,
                    "processing_time_seconds": result.statistics.processing_time_seconds,
                    "average_confidence": result.statistics.average_confidence,
                    "frames_with_damage": result.statistics.frames_with_damage
                },
                "video_metadata": {
                    "duration_seconds": result.video_metadata.duration_seconds,
                    "fps": result.video_metadata.fps,
                    "width": result.video_metadata.width,
                    "height": result.video_metadata.height,
                    "file_size_bytes": result.video_metadata.file_size_bytes,
                    "format": result.video_metadata.format,
                    "detected_damages": result.video_metadata.detected_damages
                },
                "model_version": result.model_version,
                "confidence_threshold": result.confidence_threshold,
                "created_at": result.created_at.isoformat(),
                "updated_at": result.updated_at.isoformat()
            })
        
        return DetectionResultListResponse(
            success=True,
            message=f"Retrieved {len(detection_responses)} detection results",
            data={
                "results": detection_responses,
                "pagination": {
                    "page": pagination.page,
                    "page_size": pagination.page_size,
                    "total_count": results['total_count'],
                    "total_pages": results['total_pages']
                },
                "filters_applied": filters
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get detection results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get detection results"
        )


@router.get("/{result_id}", response_model=DetectionResultResponse)
async def get_detection_result(
    result_id: str,
    container: DependencyContainer = Depends(get_dependency_container)
) -> DetectionResultResponse:
    """Get a specific detection result by ID."""
    try:
        # Get detection results service
        detection_app_service = container.get_detection_results_app_service()
        
        # Get result
        result = await detection_app_service.get_detection_result_by_id(result_id)
        
        if not result:
            raise ResourceNotFoundException("detection_result", result_id)
        
        return DetectionResultResponse(
            success=True,
            message="Detection result retrieved",
            data={
                "id": result.id,
                "video_id": result.video_id,
                "damages": [
                    {
                        "id": damage.id,
                        "type": damage.type,
                        "severity": damage.severity,
                        "confidence": damage.confidence,
                        "bounding_box": {
                            "x": damage.bounding_box.x,
                            "y": damage.bounding_box.y,
                            "width": damage.bounding_box.width,
                            "height": damage.bounding_box.height
                        },
                        "frame_number": damage.frame_number,
                        "timestamp": damage.timestamp,
                        "area_pixels": damage.area_pixels,
                        "description": damage.description
                    } for damage in result.damages
                ],
                "statistics": {
                    "total_frames_processed": result.statistics.total_frames_processed,
                    "damages_detected": result.statistics.damages_detected,
                    "processing_time_seconds": result.statistics.processing_time_seconds,
                    "average_confidence": result.statistics.average_confidence,
                    "frames_with_damage": result.statistics.frames_with_damage
                },
                "video_metadata": {
                    "duration_seconds": result.video_metadata.duration_seconds,
                    "fps": result.video_metadata.fps,
                    "width": result.video_metadata.width,
                    "height": result.video_metadata.height,
                    "file_size_bytes": result.video_metadata.file_size_bytes,
                    "format": result.video_metadata.format,
                    "detected_damages": result.video_metadata.detected_damages
                },
                "model_version": result.model_version,
                "confidence_threshold": result.confidence_threshold,
                "created_at": result.created_at.isoformat(),
                "updated_at": result.updated_at.isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get detection result {result_id}: {e}")
        if isinstance(e, (ResourceNotFoundException, HTTPException)):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get detection result"
        )


@router.get("/video/{video_id}", response_model=DetectionResultListResponse)
async def get_detection_results_by_video(
    video_id: str,
    pagination: PaginationRequest = Depends(),
    container: DependencyContainer = Depends(get_dependency_container)
) -> DetectionResultListResponse:
    """Get all detection results for a specific video."""
    try:
        # Get detection results service
        detection_app_service = container.get_detection_results_app_service()
        
        # Get results for video
        results = await detection_app_service.get_detection_results_by_video_id(
            video_id=video_id,
            page=pagination.page,
            page_size=pagination.page_size
        )
        
        if not results['results']:
            raise ResourceNotFoundException("detection_results_for_video", video_id)
        
        # Convert to response format (same as above)
        detection_responses = []
        for result in results['results']:
            detection_responses.append({
                "id": result.id,
                "video_id": result.video_id,
                "damages": [
                    {
                        "id": damage.id,
                        "type": damage.type,
                        "severity": damage.severity,
                        "confidence": damage.confidence,
                        "bounding_box": {
                            "x": damage.bounding_box.x,
                            "y": damage.bounding_box.y,
                            "width": damage.bounding_box.width,
                            "height": damage.bounding_box.height
                        },
                        "frame_number": damage.frame_number,
                        "timestamp": damage.timestamp,
                        "area_pixels": damage.area_pixels,
                        "description": damage.description
                    } for damage in result.damages
                ],
                "statistics": {
                    "total_frames_processed": result.statistics.total_frames_processed,
                    "damages_detected": result.statistics.damages_detected,
                    "processing_time_seconds": result.statistics.processing_time_seconds,
                    "average_confidence": result.statistics.average_confidence,
                    "frames_with_damage": result.statistics.frames_with_damage
                },
                "model_version": result.model_version,
                "confidence_threshold": result.confidence_threshold,
                "created_at": result.created_at.isoformat()
            })
        
        return DetectionResultListResponse(
            success=True,
            message=f"Retrieved {len(detection_responses)} detection results for video {video_id}",
            data={
                "results": detection_responses,
                "pagination": {
                    "page": pagination.page,
                    "page_size": pagination.page_size,
                    "total_count": results['total_count'],
                    "total_pages": results['total_pages']
                },
                "video_id": video_id
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get detection results for video {video_id}: {e}")
        if isinstance(e, (ResourceNotFoundException, HTTPException)):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get detection results for video"
        )


@router.get("/statistics/summary", response_model=StatisticsResponse)
async def get_detection_statistics(
    start_date: Optional[date] = Query(None, description="Statistics from this date"),
    end_date: Optional[date] = Query(None, description="Statistics until this date"),
    container: DependencyContainer = Depends(get_dependency_container)
) -> StatisticsResponse:
    """Get detection statistics summary."""
    try:
        # Get detection results service
        detection_app_service = container.get_detection_results_app_service()
        
        # Convert dates to datetime if provided
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
        
        # Get statistics
        stats = await detection_app_service.get_detection_statistics(
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        return StatisticsResponse(
            success=True,
            message="Detection statistics retrieved",
            data={
                "statistics": stats,
                "date_range": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get detection statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get detection statistics"
        )


@router.post("/search", response_model=SearchResultsResponse)
async def search_detection_results(
    request: SearchResultsRequest,
    container: DependencyContainer = Depends(get_dependency_container)
) -> SearchResultsResponse:
    """Search detection results based on various criteria."""
    try:
        # Get detection results service
        detection_app_service = container.get_detection_results_app_service()
        
        # Perform search
        results = await detection_app_service.search_detection_results(
            query=request.query,
            filters=request.filters,
            page=request.page,
            page_size=request.page_size
        )
        
        return SearchResultsResponse(
            success=True,
            message=f"Found {results['total_count']} matching results",
            data={
                "results": results['results'],
                "search_query": request.query,
                "filters": request.filters,
                "pagination": {
                    "page": request.page,
                    "page_size": request.page_size,
                    "total_count": results['total_count'],
                    "total_pages": results['total_pages']
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to search detection results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search detection results"
        )


@router.get("/trends/analysis", response_model=TrendsResponse)
async def get_damage_trends(
    period: str = Query("month", regex="^(day|week|month|year)$", description="Time period for trends"),
    damage_type: Optional[DamageType] = Query(None, description="Filter by damage type"),
    start_date: Optional[date] = Query(None, description="Trends from this date"),
    end_date: Optional[date] = Query(None, description="Trends until this date"),
    container: DependencyContainer = Depends(get_dependency_container)
) -> TrendsResponse:
    """Get damage detection trends analysis."""
    try:
        # Get detection results service
        detection_app_service = container.get_detection_results_app_service()
        
        # Convert dates to datetime if provided
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
        
        # Get trends
        trends = await detection_app_service.get_damage_trends(
            period=period,
            damage_type=damage_type,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        return TrendsResponse(
            success=True,
            message="Damage trends analysis retrieved",
            data={
                "trends": trends,
                "analysis_period": period,
                "damage_type_filter": damage_type,
                "date_range": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get damage trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get damage trends"
        )


@router.post("/export", response_model=ApiResponse)
async def export_detection_results(
    request: ExportResultsRequest,
    container: DependencyContainer = Depends(get_dependency_container)
) -> ApiResponse:
    """Export detection results to various formats."""
    try:
        # Get detection results service
        detection_app_service = container.get_detection_results_app_service()
        
        # Export results
        export_info = await detection_app_service.export_detection_results(
            format=request.format,
            filters=request.filters,
            include_images=request.include_images,
            output_path=request.output_path
        )
        
        return ApiResponse(
            success=True,
            message="Detection results exported successfully",
            data={
                "export_format": request.format,
                "file_path": export_info['file_path'],
                "file_size_bytes": export_info['file_size_bytes'],
                "records_exported": export_info['records_exported'],
                "export_time": export_info['export_time'],
                "filters_applied": request.filters
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to export detection results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export detection results"
        )


@router.delete("/{result_id}", response_model=ApiResponse)
async def delete_detection_result(
    result_id: str,
    container: DependencyContainer = Depends(get_dependency_container)
) -> ApiResponse:
    """Delete a specific detection result."""
    try:
        # Get detection repository
        detection_repo = container.get_detection_repository()
        
        # Check if result exists
        result = detection_repo.find_by_id(result_id)
        if not result:
            raise ResourceNotFoundException("detection_result", result_id)
        
        # Delete result
        detection_repo.delete(result_id)
        
        return ApiResponse(
            success=True,
            message="Detection result deleted successfully",
            data={
                "result_id": result_id,
                "video_id": result.video_id
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to delete detection result {result_id}: {e}")
        if isinstance(e, (ResourceNotFoundException, HTTPException)):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete detection result"
        )