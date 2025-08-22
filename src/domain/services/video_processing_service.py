from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, AsyncGenerator
from pathlib import Path
import numpy as np

from ..entities.video import Video, VideoMetadata
from ..entities.detection_result import DetectionResult


class VideoProcessingService(ABC):
    """Interfaz del servicio de procesamiento de video."""
    
    @abstractmethod
    async def extract_metadata(self, video_path: Path) -> VideoMetadata:
        """Extrae metadatos de un video."""
        pass
    
    @abstractmethod
    async def validate_video(self, video_path: Path) -> bool:
        """Valida si un archivo de video es válido y procesable."""
        pass
    
    @abstractmethod
    async def extract_frames(self, video: Video, frame_interval: int = 1) -> AsyncGenerator[Tuple[int, np.ndarray], None]:
        """Extrae frames de un video de forma asíncrona."""
        pass
    
    @abstractmethod
    async def get_frame_at_time(self, video: Video, timestamp: float) -> Optional[np.ndarray]:
        """Obtiene un frame específico en un tiempo dado."""
        pass
    
    @abstractmethod
    async def get_frame_at_number(self, video: Video, frame_number: int) -> Optional[np.ndarray]:
        """Obtiene un frame específico por número."""
        pass
    
    @abstractmethod
    async def create_annotated_video(self, video: Video, detection_result: DetectionResult, output_path: Path) -> Path:
        """Crea un video anotado con las detecciones."""
        pass
    
    @abstractmethod
    async def create_thumbnail(self, video: Video, output_path: Path, timestamp: float = 0.0) -> Path:
        """Crea una miniatura del video."""
        pass
    
    @abstractmethod
    async def get_video_info(self, video_path: Path) -> dict:
        """Obtiene información detallada del video."""
        pass
    
    @abstractmethod
    async def compress_video(self, input_path: Path, output_path: Path, quality: str = 'medium') -> Path:
        """Comprime un video."""
        pass
    
    @abstractmethod
    async def convert_format(self, input_path: Path, output_path: Path, target_format: str) -> Path:
        """Convierte un video a otro formato."""
        pass
    
    @abstractmethod
    async def get_supported_formats(self) -> List[str]:
        """Obtiene los formatos de video soportados."""
        pass