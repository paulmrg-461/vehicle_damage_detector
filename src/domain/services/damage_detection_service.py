from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path

from ..entities.video import Video
from ..entities.damage import Damage
from ..entities.detection_result import DetectionResult


class DamageDetectionService(ABC):
    """Interfaz del servicio de detección de daños."""
    
    @abstractmethod
    async def detect_damages_in_video(self, video: Video, confidence_threshold: float = 0.5) -> DetectionResult:
        """Detecta daños en un video completo."""
        pass
    
    @abstractmethod
    async def detect_damages_in_frame(self, frame_data: bytes, frame_number: int) -> List[Damage]:
        """Detecta daños en un frame específico."""
        pass
    
    @abstractmethod
    async def load_model(self, model_path: Optional[Path] = None) -> bool:
        """Carga el modelo de detección."""
        pass
    
    @abstractmethod
    async def is_model_loaded(self) -> bool:
        """Verifica si el modelo está cargado."""
        pass
    
    @abstractmethod
    async def get_model_info(self) -> dict:
        """Obtiene información del modelo cargado."""
        pass
    
    @abstractmethod
    async def set_confidence_threshold(self, threshold: float) -> None:
        """Establece el umbral de confianza para las detecciones."""
        pass
    
    @abstractmethod
    async def get_supported_formats(self) -> List[str]:
        """Obtiene los formatos de video soportados."""
        pass