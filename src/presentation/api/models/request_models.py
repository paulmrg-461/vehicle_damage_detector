from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field, validator
from pathlib import Path

from src.domain.entities.damage import DamageType, DamageSeverity
from src.domain.entities.video import VideoStatus


class ProcessVideoRequest(BaseModel):
    """Modelo de solicitud para procesar un video."""
    video_path: str = Field(description="Ruta del archivo de video a procesar")
    confidence_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Umbral de confianza para detecciones (0.0-1.0)"
    )
    create_annotated_video: Optional[bool] = Field(
        default=True,
        description="Indica si crear video anotado con detecciones"
    )
    create_thumbnail: Optional[bool] = Field(
        default=True,
        description="Indica si crear miniatura del video"
    )
    
    @validator('video_path')
    def validate_video_path(cls, v):
        if not v or not v.strip():
            raise ValueError('La ruta del video no puede estar vacía')
        return v.strip()


class ProcessMultipleVideosRequest(BaseModel):
    """Modelo de solicitud para procesar múltiples videos."""
    video_paths: List[str] = Field(description="Lista de rutas de archivos de video")
    confidence_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Umbral de confianza para detecciones (0.0-1.0)"
    )
    create_annotated_videos: Optional[bool] = Field(
        default=True,
        description="Indica si crear videos anotados"
    )
    create_thumbnails: Optional[bool] = Field(
        default=True,
        description="Indica si crear miniaturas"
    )
    
    @validator('video_paths')
    def validate_video_paths(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Debe proporcionar al menos una ruta de video')
        
        # Validar que no haya rutas vacías
        for path in v:
            if not path or not path.strip():
                raise ValueError('Las rutas de video no pueden estar vacías')
        
        return [path.strip() for path in v]


class GetDetectionResultsRequest(BaseModel):
    """Modelo de solicitud para obtener resultados de detección."""
    video_id: Optional[str] = Field(None, description="ID del video específico")
    start_date: Optional[date] = Field(None, description="Fecha de inicio para filtrar")
    end_date: Optional[date] = Field(None, description="Fecha de fin para filtrar")
    damage_type: Optional[DamageType] = Field(None, description="Tipo de daño para filtrar")
    min_severity: Optional[DamageSeverity] = Field(None, description="Severidad mínima para filtrar")
    min_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confianza mínima para filtrar"
    )
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return v


class UpdateConfidenceThresholdRequest(BaseModel):
    """Modelo de solicitud para actualizar el umbral de confianza."""
    confidence_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="Nuevo umbral de confianza (0.0-1.0)"
    )


class SearchResultsRequest(BaseModel):
    """Modelo de solicitud para búsqueda de resultados."""
    query: str = Field(description="Consulta de búsqueda")
    search_in_video_path: Optional[bool] = Field(
        default=True,
        description="Buscar en rutas de video"
    )
    search_in_model_version: Optional[bool] = Field(
        default=True,
        description="Buscar en versión del modelo"
    )
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('La consulta de búsqueda no puede estar vacía')
        return v.strip()


class GetTrendsRequest(BaseModel):
    """Modelo de solicitud para obtener tendencias."""
    days: Optional[int] = Field(
        default=30,
        ge=1,
        le=365,
        description="Número de días para analizar (1-365)"
    )


class CleanupFilesRequest(BaseModel):
    """Modelo de solicitud para limpieza de archivos."""
    older_than_days: Optional[int] = Field(
        default=7,
        ge=1,
        description="Eliminar archivos más antiguos que N días"
    )


class ValidateVideoFileRequest(BaseModel):
    """Modelo de solicitud para validar archivo de video."""
    file_path: str = Field(description="Ruta del archivo a validar")
    
    @validator('file_path')
    def validate_file_path(cls, v):
        if not v or not v.strip():
            raise ValueError('La ruta del archivo no puede estar vacía')
        return v.strip()


class CopyVideoRequest(BaseModel):
    """Modelo de solicitud para copiar video al workspace."""
    source_path: str = Field(description="Ruta del archivo fuente")
    filename: Optional[str] = Field(None, description="Nombre del archivo de destino")
    
    @validator('source_path')
    def validate_source_path(cls, v):
        if not v or not v.strip():
            raise ValueError('La ruta fuente no puede estar vacía')
        return v.strip()
    
    @validator('filename')
    def validate_filename(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('El nombre del archivo no puede estar vacío')
            # Validar caracteres no permitidos en nombres de archivo
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
            if any(char in v for char in invalid_chars):
                raise ValueError(f'El nombre del archivo contiene caracteres no válidos: {", ".join(invalid_chars)}')
        return v


class MoveVideoRequest(BaseModel):
    """Modelo de solicitud para mover video al workspace."""
    source_path: str = Field(description="Ruta del archivo fuente")
    filename: Optional[str] = Field(None, description="Nombre del archivo de destino")
    
    @validator('source_path')
    def validate_source_path(cls, v):
        if not v or not v.strip():
            raise ValueError('La ruta fuente no puede estar vacía')
        return v.strip()
    
    @validator('filename')
    def validate_filename(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('El nombre del archivo no puede estar vacío')
            # Validar caracteres no permitidos en nombres de archivo
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
            if any(char in v for char in invalid_chars):
                raise ValueError(f'El nombre del archivo contiene caracteres no válidos: {", ".join(invalid_chars)}')
        return v


class DiscoverVideosRequest(BaseModel):
    """Modelo de solicitud para descubrir videos en directorio."""
    directory_path: str = Field(description="Ruta del directorio a explorar")
    
    @validator('directory_path')
    def validate_directory_path(cls, v):
        if not v or not v.strip():
            raise ValueError('La ruta del directorio no puede estar vacía')
        return v.strip()


class ListFilesRequest(BaseModel):
    """Modelo de solicitud para listar archivos."""
    directory_path: str = Field(description="Ruta del directorio")
    file_extensions: Optional[List[str]] = Field(
        None,
        description="Extensiones de archivo a filtrar (ej: ['.mp4', '.avi'])"
    )
    
    @validator('directory_path')
    def validate_directory_path(cls, v):
        if not v or not v.strip():
            raise ValueError('La ruta del directorio no puede estar vacía')
        return v.strip()
    
    @validator('file_extensions')
    def validate_file_extensions(cls, v):
        if v is not None:
            # Asegurar que las extensiones empiecen con punto
            validated_extensions = []
            for ext in v:
                ext = ext.strip().lower()
                if not ext.startswith('.'):
                    ext = '.' + ext
                validated_extensions.append(ext)
            return validated_extensions
        return v


class ExportResultsRequest(BaseModel):
    """Modelo de solicitud para exportar resultados."""
    video_ids: Optional[List[str]] = Field(None, description="IDs de videos específicos")
    start_date: Optional[date] = Field(None, description="Fecha de inicio")
    end_date: Optional[date] = Field(None, description="Fecha de fin")
    format: Optional[str] = Field(
        default="json",
        description="Formato de exportación (json, csv)"
    )
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['json', 'csv']
        if v.lower() not in allowed_formats:
            raise ValueError(f'Formato no soportado. Formatos permitidos: {", ".join(allowed_formats)}')
        return v.lower()
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return v


# Modelos para paginación
class PaginationRequest(BaseModel):
    """Modelo base para solicitudes con paginación."""
    page: Optional[int] = Field(
        default=1,
        ge=1,
        description="Número de página (empezando en 1)"
    )
    page_size: Optional[int] = Field(
        default=20,
        ge=1,
        le=100,
        description="Tamaño de página (1-100)"
    )


class GetVideosRequest(PaginationRequest):
    """Modelo de solicitud para obtener lista de videos."""
    status: Optional[VideoStatus] = Field(None, description="Filtrar por estado")
    search: Optional[str] = Field(None, description="Búsqueda en nombre de archivo")
    
    @validator('search')
    def validate_search(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class GetDetectionResultsPaginatedRequest(PaginationRequest):
    """Modelo de solicitud paginada para resultados de detección."""
    video_id: Optional[str] = Field(None, description="ID del video específico")
    start_date: Optional[date] = Field(None, description="Fecha de inicio")
    end_date: Optional[date] = Field(None, description="Fecha de fin")
    damage_type: Optional[DamageType] = Field(None, description="Tipo de daño")
    min_severity: Optional[DamageSeverity] = Field(None, description="Severidad mínima")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return v


class UpdateConfidenceRequest(BaseModel):
    """Modelo de solicitud para actualizar el umbral de confianza."""
    confidence_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="Nuevo umbral de confianza para detecciones (0.0-1.0)"
    )


class ValidateVideoRequest(BaseModel):
    """Modelo de solicitud para validar un archivo de video."""
    video_path: str = Field(description="Ruta del archivo de video a validar")
    
    @validator('video_path')
    def validate_video_path(cls, v):
        if not v or not v.strip():
            raise ValueError('La ruta del video no puede estar vacía')
        return v.strip()


class CleanupRequest(BaseModel):
    """Modelo de solicitud para limpiar archivos temporales."""
    older_than_days: Optional[int] = Field(
        default=7,
        ge=1,
        description="Eliminar archivos más antiguos que X días"
    )
    include_logs: Optional[bool] = Field(
        default=False,
        description="Incluir archivos de log en la limpieza"
    )
    include_outputs: Optional[bool] = Field(
        default=False,
        description="Incluir archivos de salida en la limpieza"
    )