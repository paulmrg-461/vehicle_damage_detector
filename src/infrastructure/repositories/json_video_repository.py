import json
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import logging

from ...domain.entities.video import Video, VideoStatus, VideoFormat, VideoMetadata
from ...domain.repositories.video_repository import VideoRepository


class JsonVideoRepository(VideoRepository):
    """Implementación del repositorio de videos usando archivos JSON."""
    
    def __init__(self, storage_path: Path):
        self._storage_path = storage_path
        self._videos_file = storage_path / "videos.json"
        self._logger = logging.getLogger(__name__)
        
        # Asegurar que el directorio existe
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Inicializar archivo si no existe
        if not self._videos_file.exists():
            self._save_data({})
    
    async def save(self, video: Video) -> Video:
        """Guarda un video en el repositorio."""
        try:
            data = await self._load_data()
            data[video.id] = self._video_to_dict(video)
            await self._save_data(data)
            
            self._logger.info(f"Video guardado: {video.id} - {video.name}")
            return video
            
        except Exception as e:
            self._logger.error(f"Error al guardar video {video.id}: {e}")
            raise e
    
    async def find_by_id(self, video_id: str) -> Optional[Video]:
        """Busca un video por su ID."""
        try:
            data = await self._load_data()
            video_data = data.get(video_id)
            
            if video_data:
                return self._dict_to_video(video_data)
            return None
            
        except Exception as e:
            self._logger.error(f"Error al buscar video {video_id}: {e}")
            return None
    
    async def find_by_path(self, file_path: Path) -> Optional[Video]:
        """Busca un video por su ruta de archivo."""
        try:
            data = await self._load_data()
            
            for video_data in data.values():
                if Path(video_data['file_path']) == file_path:
                    return self._dict_to_video(video_data)
            
            return None
            
        except Exception as e:
            self._logger.error(f"Error al buscar video por ruta {file_path}: {e}")
            return None
    
    async def find_all(self) -> List[Video]:
        """Obtiene todos los videos."""
        try:
            data = await self._load_data()
            videos = []
            
            for video_data in data.values():
                video = self._dict_to_video(video_data)
                videos.append(video)
            
            return videos
            
        except Exception as e:
            self._logger.error(f"Error al obtener todos los videos: {e}")
            return []
    
    async def find_by_status(self, status: str) -> List[Video]:
        """Busca videos por su estado."""
        try:
            data = await self._load_data()
            videos = []
            
            for video_data in data.values():
                if video_data['status'] == status:
                    video = self._dict_to_video(video_data)
                    videos.append(video)
            
            return videos
            
        except Exception as e:
            self._logger.error(f"Error al buscar videos por estado {status}: {e}")
            return []
    
    async def update(self, video: Video) -> Video:
        """Actualiza un video existente."""
        try:
            data = await self._load_data()
            
            if video.id not in data:
                raise ValueError(f"Video no encontrado: {video.id}")
            
            data[video.id] = self._video_to_dict(video)
            await self._save_data(data)
            
            self._logger.info(f"Video actualizado: {video.id} - {video.name}")
            return video
            
        except Exception as e:
            self._logger.error(f"Error al actualizar video {video.id}: {e}")
            raise e
    
    async def delete(self, video_id: str) -> bool:
        """Elimina un video del repositorio."""
        try:
            data = await self._load_data()
            
            if video_id in data:
                del data[video_id]
                await self._save_data(data)
                self._logger.info(f"Video eliminado: {video_id}")
                return True
            
            return False
            
        except Exception as e:
            self._logger.error(f"Error al eliminar video {video_id}: {e}")
            return False
    
    async def exists(self, video_id: str) -> bool:
        """Verifica si existe un video con el ID dado."""
        try:
            data = await self._load_data()
            return video_id in data
            
        except Exception as e:
            self._logger.error(f"Error al verificar existencia del video {video_id}: {e}")
            return False
    
    async def _load_data(self) -> Dict[str, Any]:
        """Carga datos del archivo JSON."""
        try:
            with open(self._videos_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    async def _save_data(self, data: Dict[str, Any]) -> None:
        """Guarda datos en el archivo JSON."""
        with open(self._videos_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def _video_to_dict(self, video: Video) -> Dict[str, Any]:
        """Convierte un objeto Video a diccionario."""
        return {
            'id': video.id,
            'name': video.name,
            'file_path': str(video.file_path),
            'status': video.status.value,
            'created_at': video.created_at.isoformat(),
            'updated_at': video.updated_at.isoformat() if video.updated_at else None,
            'metadata': {
                'duration': video.metadata.duration,
                'fps': video.metadata.fps,
                'width': video.metadata.width,
                'height': video.metadata.height,
                'frame_count': video.metadata.frame_count,
                'file_size': video.metadata.file_size,
                'format': video.metadata.format.value,
                'codec': video.metadata.codec,
                'bitrate': video.metadata.bitrate
            } if video.metadata else None,
            'damages': [damage.to_dict() for damage in video.damages] if video.damages else []
        }
    
    def _dict_to_video(self, data: Dict[str, Any]) -> Video:
        """Convierte un diccionario a objeto Video."""
        # Crear metadata si existe
        metadata = None
        if data.get('metadata'):
            metadata_data = data['metadata']
            metadata = VideoMetadata(
                duration=metadata_data['duration'],
                fps=metadata_data['fps'],
                width=metadata_data['width'],
                height=metadata_data['height'],
                frame_count=metadata_data['frame_count'],
                file_size=metadata_data['file_size'],
                format=VideoFormat(metadata_data['format']),
                codec=metadata_data['codec'],
                bitrate=metadata_data['bitrate']
            )
        
        # Crear video
        video = Video(
            id=data['id'],
            name=data['name'],
            file_path=Path(data['file_path']),
            status=VideoStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            metadata=metadata,
            damages=[]  # Los daños se cargan por separado si es necesario
        )
        
        return video