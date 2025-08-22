from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from enum import Enum

from .damage import Damage


class VideoStatus(Enum):
    """Estados posibles de procesamiento de un video."""
    PENDING = "pending"        # Pendiente de procesar
    PROCESSING = "processing"  # En proceso
    COMPLETED = "completed"    # Completado exitosamente
    FAILED = "failed"          # Falló el procesamiento
    CANCELLED = "cancelled"    # Cancelado


class VideoFormat(Enum):
    """Formatos de video soportados."""
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    MKV = "mkv"
    WMV = "wmv"
    FLV = "flv"
    WEBM = "webm"
    UNKNOWN = "unknown"


@dataclass
class VideoMetadata:
    """Metadatos del video."""
    duration: float  # Duración en segundos
    fps: float       # Frames por segundo
    width: int       # Ancho en píxeles
    height: int      # Alto en píxeles
    frame_count: int # Total de frames
    format: VideoFormat
    file_size: int   # Tamaño en bytes
    codec: str = "Unknown"  # Codec del video
    bitrate: int = 0  # Bitrate en bits por segundo
    
    def __post_init__(self):
        """Validar metadatos."""
        if self.duration <= 0:
            raise ValueError("La duración debe ser positiva")
        if self.fps <= 0:
            raise ValueError("Los FPS deben ser positivos")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Las dimensiones deben ser positivas")
        if self.frame_count <= 0:
            raise ValueError("El total de frames debe ser positivo")
        if self.file_size <= 0:
            raise ValueError("El tamaño del archivo debe ser positivo")
    
    @property
    def resolution(self) -> str:
        """Obtiene la resolución como string."""
        return f"{self.width}x{self.height}"
    
    @property
    def aspect_ratio(self) -> float:
        """Calcula la relación de aspecto."""
        return self.width / self.height


@dataclass
class Video:
    """Entidad que representa un video a procesar."""
    id: str
    file_path: Path
    name: str
    status: VideoStatus
    created_at: datetime
    metadata: Optional[VideoMetadata] = None
    damages: List[Damage] = None
    processed_at: Optional[datetime] = None
    processing_time: Optional[float] = None  # Tiempo en segundos
    error_message: Optional[str] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Inicializar valores por defecto."""
        if self.damages is None:
            self.damages = []
        
        # Validar que el archivo existe
        if not self.file_path.exists():
            raise FileNotFoundError(f"El archivo {self.file_path} no existe")
        
        # Validar formato del archivo
        if self.file_path.suffix.lower() not in ['.mp4', '.avi', '.mov', '.mkv']:
            raise ValueError(f"Formato de archivo no soportado: {self.file_path.suffix}")
    
    @property
    def is_processed(self) -> bool:
        """Verifica si el video ha sido procesado."""
        return self.status == VideoStatus.COMPLETED
    
    @property
    def has_damages(self) -> bool:
        """Verifica si se encontraron daños en el video."""
        return len(self.damages) > 0
    
    @property
    def damage_count(self) -> int:
        """Obtiene el número total de daños detectados."""
        return len(self.damages)
    
    @property
    def high_confidence_damages(self) -> List[Damage]:
        """Obtiene solo los daños con alta confianza."""
        return [damage for damage in self.damages if damage.is_high_confidence()]
    
    @property
    def severe_damages(self) -> List[Damage]:
        """Obtiene solo los daños severos o críticos."""
        return [damage for damage in self.damages if damage.is_severe()]
    
    def add_damage(self, damage: Damage) -> None:
        """Añade un daño detectado al video."""
        self.damages.append(damage)
    
    def mark_as_processing(self) -> None:
        """Marca el video como en proceso."""
        self.status = VideoStatus.PROCESSING
    
    def mark_as_completed(self, processing_time: float) -> None:
        """Marca el video como completado."""
        self.status = VideoStatus.COMPLETED
        self.processed_at = datetime.now()
        self.processing_time = processing_time
        self.error_message = None
    
    def mark_as_failed(self, error_message: str) -> None:
        """Marca el video como fallido."""
        self.status = VideoStatus.FAILED
        self.processed_at = datetime.now()
        self.error_message = error_message
    
    def to_dict(self) -> dict:
        """Convierte el video a diccionario para serialización."""
        return {
            "id": self.id,
            "file_path": str(self.file_path),
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "metadata": {
                "duration": self.metadata.duration,
                "fps": self.metadata.fps,
                "width": self.metadata.width,
                "height": self.metadata.height,
                "total_frames": self.metadata.total_frames,
                "format": self.metadata.format.value,
                "file_size": self.metadata.file_size
            } if self.metadata else None,
            "damages": [damage.to_dict() for damage in self.damages],
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "processing_time": self.processing_time,
            "error_message": self.error_message,
            "damage_count": self.damage_count,
            "has_damages": self.has_damages
        }