from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime

from ..entities.detection_result import DetectionResult
from ..entities.damage import Damage


class DetectionRepository(ABC):
    """Interfaz del repositorio para gestionar resultados de detección."""
    
    @abstractmethod
    async def save(self, detection_result: DetectionResult) -> DetectionResult:
        """Guarda un resultado de detección."""
        pass
    
    @abstractmethod
    async def find_by_id(self, result_id: str) -> Optional[DetectionResult]:
        """Busca un resultado por su ID."""
        pass
    
    @abstractmethod
    async def find_by_video_id(self, video_id: str) -> List[DetectionResult]:
        """Busca resultados por ID de video."""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[DetectionResult]:
        """Obtiene todos los resultados de detección."""
        pass
    
    @abstractmethod
    async def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[DetectionResult]:
        """Busca resultados en un rango de fechas."""
        pass
    
    @abstractmethod
    async def find_with_damages(self) -> List[DetectionResult]:
        """Busca resultados que contengan daños detectados."""
        pass
    
    @abstractmethod
    async def find_by_damage_type(self, damage_type: str) -> List[DetectionResult]:
        """Busca resultados que contengan un tipo específico de daño."""
        pass
    
    @abstractmethod
    async def update(self, detection_result: DetectionResult) -> DetectionResult:
        """Actualiza un resultado de detección."""
        pass
    
    @abstractmethod
    async def delete(self, result_id: str) -> bool:
        """Elimina un resultado de detección."""
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, any]:
        """Obtiene estadísticas generales de detecciones."""
        pass
    
    @abstractmethod
    async def exists(self, result_id: str) -> bool:
        """Verifica si existe un resultado con el ID dado."""
        pass