from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from src.domain.entities.damage import DamageType, DamageSeverity
from src.domain.entities.video import VideoStatus, VideoFormat


class ApiResponse(BaseModel):
    """Modelo base para respuestas de la API."""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    success: bool = Field(description="Indica si la operación fue exitosa")
    message: str = Field(description="Mensaje descriptivo de la respuesta")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de la respuesta")


class ErrorResponse(ApiResponse):
    """Modelo para respuestas de error."""
    success: bool = Field(default=False)
    error_code: Optional[str] = Field(None, description="Código de error específico")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales del error")
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class BoundingBoxResponse(BaseModel):
    """Modelo de respuesta para bounding box."""
    x: float = Field(description="Coordenada X del punto superior izquierdo")
    y: float = Field(description="Coordenada Y del punto superior izquierdo")
    width: float = Field(description="Ancho del bounding box")
    height: float = Field(description="Alto del bounding box")


class DamageResponse(BaseModel):
    """Modelo de respuesta para daños detectados."""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    damage_type: DamageType = Field(description="Tipo de daño detectado")
    severity: DamageSeverity = Field(description="Severidad del daño")
    confidence: float = Field(description="Confianza de la detección (0-1)")
    bounding_box: BoundingBoxResponse = Field(description="Coordenadas del área dañada")
    frame_number: int = Field(description="Número de frame donde se detectó")
    timestamp: datetime = Field(description="Timestamp de la detección")


class VideoMetadataResponse(BaseModel):
    """Modelo de respuesta para metadatos de video."""
    file_path: str = Field(description="Ruta del archivo de video")
    duration_seconds: float = Field(description="Duración del video en segundos")
    fps: float = Field(description="Frames por segundo")
    width: int = Field(description="Ancho del video en píxeles")
    height: int = Field(description="Alto del video en píxeles")
    format: VideoFormat = Field(description="Formato del video")
    file_size_mb: float = Field(description="Tamaño del archivo en MB")


class DetectionStatisticsResponse(BaseModel):
    """Modelo de respuesta para estadísticas de detección."""
    total_frames_processed: int = Field(description="Total de frames procesados")
    frames_with_damage: int = Field(description="Frames con daños detectados")
    total_damages_detected: int = Field(description="Total de daños detectados")
    processing_time_seconds: float = Field(description="Tiempo de procesamiento en segundos")
    average_confidence: float = Field(description="Confianza promedio de las detecciones")


class VideoResponse(BaseModel):
    """Modelo de respuesta para información de video."""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    id: str = Field(description="ID único del video")
    file_path: str = Field(description="Ruta del archivo de video")
    status: VideoStatus = Field(description="Estado actual del video")
    created_at: datetime = Field(description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")
    metadata: Optional[VideoMetadataResponse] = Field(None, description="Metadatos del video")


class DetectionResultResponse(BaseModel):
    """Modelo de respuesta para resultados de detección."""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    id: str = Field(description="ID único del resultado")
    video_id: str = Field(description="ID del video procesado")
    damages: List[DamageResponse] = Field(description="Lista de daños detectados")
    statistics: DetectionStatisticsResponse = Field(description="Estadísticas del procesamiento")
    video_metadata: Optional[VideoMetadataResponse] = Field(None, description="Metadatos del video")
    model_version: str = Field(description="Versión del modelo utilizado")
    confidence_threshold: float = Field(description="Umbral de confianza utilizado")
    created_at: datetime = Field(description="Fecha de creación del resultado")
    annotated_video_path: Optional[str] = Field(None, description="Ruta del video anotado")
    thumbnail_path: Optional[str] = Field(None, description="Ruta de la miniatura")


class ProcessVideoResponse(ApiResponse):
    """Modelo de respuesta para procesamiento de video."""
    video_id: str = Field(description="ID del video procesado")
    detection_result: DetectionResultResponse = Field(description="Resultado de la detección")


class VideoListResponse(ApiResponse):
    """Modelo de respuesta para lista de videos."""
    videos: List[VideoResponse] = Field(description="Lista de videos")
    total_count: int = Field(description="Número total de videos")


class DetectionResultListResponse(ApiResponse):
    """Modelo de respuesta para lista de resultados de detección."""
    results: List[DetectionResultResponse] = Field(description="Lista de resultados")
    total_count: int = Field(description="Número total de resultados")


class FileValidationResponse(BaseModel):
    """Modelo de respuesta para validación de archivos."""
    is_valid: bool = Field(description="Indica si el archivo es válido")
    file_exists: bool = Field(description="Indica si el archivo existe")
    is_supported_format: bool = Field(description="Indica si el formato es soportado")
    size_valid: bool = Field(description="Indica si el tamaño es válido")
    file_size_mb: float = Field(description="Tamaño del archivo en MB")
    mime_type: Optional[str] = Field(None, description="Tipo MIME del archivo")
    errors: List[str] = Field(description="Lista de errores de validación")


class ProcessingStatusResponse(BaseModel):
    """Modelo de respuesta para estado de procesamiento."""
    max_concurrent_processes: int = Field(description="Máximo de procesos concurrentes")
    currently_processing: int = Field(description="Videos siendo procesados actualmente")
    processing_videos: List[str] = Field(description="Lista de videos en procesamiento")
    available_slots: int = Field(description="Slots disponibles para procesamiento")


class StatisticsResponse(BaseModel):
    """Modelo de respuesta para estadísticas generales."""
    total_videos_processed: int = Field(description="Total de videos procesados")
    total_damages_detected: int = Field(description="Total de daños detectados")
    damage_type_distribution: Dict[str, int] = Field(description="Distribución por tipo de daño")
    severity_distribution: Dict[str, int] = Field(description="Distribución por severidad")
    average_processing_time: float = Field(description="Tiempo promedio de procesamiento")
    most_common_damage_type: Optional[str] = Field(None, description="Tipo de daño más común")
    processing_success_rate: float = Field(description="Tasa de éxito en procesamiento")


class HealthCheckResponse(BaseModel):
    """Modelo de respuesta para health check."""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    status: str = Field(description="Estado general del sistema")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, bool] = Field(description="Estado de los servicios")
    version: str = Field(description="Versión de la aplicación")
    uptime_seconds: Optional[float] = Field(None, description="Tiempo de actividad en segundos")


class DiskUsageResponse(BaseModel):
    """Modelo de respuesta para uso de disco."""
    directories: Dict[str, Dict[str, Any]] = Field(description="Información de directorios")
    disk_usage: Dict[str, float] = Field(description="Uso general del disco")
    total_app_size_mb: float = Field(description="Tamaño total de la aplicación en MB")


class BackupResponse(ApiResponse):
    """Modelo de respuesta para operaciones de backup."""
    backup_path: str = Field(description="Ruta del backup creado")
    backup_size_mb: Optional[float] = Field(None, description="Tamaño del backup en MB")


class CleanupResponse(ApiResponse):
    """Modelo de respuesta para operaciones de limpieza."""
    deleted_files_count: int = Field(description="Número de archivos eliminados")
    total_size_freed_mb: float = Field(description="Espacio liberado en MB")
    older_than_days: int = Field(description="Archivos más antiguos que N días")


class SearchResultsResponse(BaseModel):
    """Modelo de respuesta para búsquedas."""
    query: str = Field(description="Consulta de búsqueda")
    results: List[DetectionResultResponse] = Field(description="Resultados encontrados")
    total_matches: int = Field(description="Total de coincidencias")
    search_time_ms: float = Field(description="Tiempo de búsqueda en milisegundos")


class TrendsResponse(BaseModel):
    """Modelo de respuesta para tendencias de daños."""
    period: str = Field(description="Período analizado")
    total_days: int = Field(description="Total de días analizados")
    daily_statistics: Dict[str, Dict[str, Any]] = Field(description="Estadísticas diarias")
    summary: Dict[str, Any] = Field(description="Resumen del período")


class ModelInfoResponse(BaseModel):
    """Modelo de respuesta para información del modelo."""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    model_name: str = Field(description="Nombre del modelo")
    model_version: str = Field(description="Versión del modelo")
    is_loaded: bool = Field(description="Indica si el modelo está cargado")
    device: str = Field(description="Dispositivo utilizado (CPU/GPU)")
    confidence_threshold: float = Field(description="Umbral de confianza actual")
    supported_classes: List[str] = Field(description="Clases soportadas por el modelo")


class FileListResponse(BaseModel):
    """Modelo de respuesta para listado de archivos."""
    files: List[Dict[str, Any]] = Field(description="Lista de archivos")
    directory_path: str = Field(description="Ruta del directorio")
    total_files: int = Field(description="Total de archivos")
    total_size_mb: float = Field(description="Tamaño total en MB")


# Modelos para paginación
class PaginationInfo(BaseModel):
    """Información de paginación."""
    page: int = Field(description="Página actual")
    page_size: int = Field(description="Tamaño de página")
    total_items: int = Field(description="Total de elementos")
    total_pages: int = Field(description="Total de páginas")
    has_next: bool = Field(description="Indica si hay página siguiente")
    has_previous: bool = Field(description="Indica si hay página anterior")


class PaginatedResponse(BaseModel):
    """Modelo base para respuestas paginadas."""
    pagination: PaginationInfo = Field(description="Información de paginación")
    data: List[Any] = Field(description="Datos de la página actual")


class PaginatedVideoListResponse(PaginatedResponse):
    """Respuesta paginada para lista de videos."""
    data: List[VideoResponse] = Field(description="Videos de la página actual")


class PaginatedDetectionResultListResponse(PaginatedResponse):
    """Respuesta paginada para lista de resultados de detección."""
    data: List[DetectionResultResponse] = Field(description="Resultados de la página actual")