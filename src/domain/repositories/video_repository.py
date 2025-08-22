from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path

from ..entities.video import Video


class VideoRepository(ABC):
    """Interfaz del repositorio para gestionar videos."""
    
    @abstractmethod
    async def save(self, video: Video) -> Video:
        """Guarda un video en el repositorio."""
        pass
    
    @abstractmethod
    async def find_by_id(self, video_id: str) -> Optional[Video]:
        """Busca un video por su ID."""
        pass
    
    @abstractmethod
    async def find_by_path(self, file_path: Path) -> Optional[Video]:
        """Busca un video por su ruta de archivo."""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Video]:
        """Obtiene todos los videos."""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: str) -> List[Video]:
        """Busca videos por su estado."""
        pass
    
    @abstractmethod
    async def update(self, video: Video) -> Video:
        """Actualiza un video existente."""
        pass
    
    @abstractmethod
    async def delete(self, video_id: str) -> bool:
        """Elimina un video del repositorio."""
        pass
    
    @abstractmethod
    async def exists(self, video_id: str) -> bool:
        """Verifica si existe un video con el ID dado."""
        pass