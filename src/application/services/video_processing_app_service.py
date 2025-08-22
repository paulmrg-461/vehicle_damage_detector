from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.domain.entities.video import Video, VideoStatus
from src.domain.entities.detection_result import DetectionResult
from src.domain.use_cases.process_video_use_case import ProcessVideoUseCase
from src.domain.use_cases.get_detection_results_use_case import GetDetectionResultsUseCase
from src.infrastructure.config.logging_config import LoggerMixin
from src.infrastructure.config.settings import get_settings


class VideoProcessingAppService(LoggerMixin):
    """Servicio de aplicación para el procesamiento de videos."""
    
    def __init__(
        self,
        process_video_use_case: ProcessVideoUseCase,
        get_detection_results_use_case: GetDetectionResultsUseCase,
        max_concurrent_processes: int = None
    ):
        self.process_video_use_case = process_video_use_case
        self.get_detection_results_use_case = get_detection_results_use_case
        self.settings = get_settings()
        self.max_concurrent_processes = (
            max_concurrent_processes or self.settings.max_concurrent_detections
        )
        self.executor = ThreadPoolExecutor(max_workers=self.max_concurrent_processes)
        self._processing_videos: Dict[str, bool] = {}
        
        self.log_info(f"VideoProcessingAppService inicializado con {self.max_concurrent_processes} procesos concurrentes")
    
    async def process_single_video(self, video_path: Path) -> DetectionResult:
        """Procesa un solo video de forma asíncrona."""
        video_path_str = str(video_path)
        
        if video_path_str in self._processing_videos:
            raise ValueError(f"El video {video_path} ya está siendo procesado")
        
        if not video_path.exists():
            raise FileNotFoundError(f"El archivo de video no existe: {video_path}")
        
        if not self.settings.is_supported_format(video_path):
            raise ValueError(f"Formato de video no soportado: {video_path.suffix}")
        
        # Verificar tamaño del archivo
        file_size = video_path.stat().st_size
        if file_size > self.settings.max_video_size_bytes:
            raise ValueError(
                f"El archivo es demasiado grande: {file_size / (1024*1024):.2f}MB. "
                f"Máximo permitido: {self.settings.max_video_size_mb}MB"
            )
        
        self._processing_videos[video_path_str] = True
        self.log_info(f"Iniciando procesamiento de video: {video_path}")
        
        try:
            # Ejecutar el procesamiento de forma asíncrona
            result = await self.process_video_use_case.execute(
                video_path=video_path,
                confidence_threshold=self.settings.confidence_threshold
            )
            
            self.log_info(f"Video procesado exitosamente: {video_path}")
            return result
            
        except Exception as e:
            self.log_error(f"Error procesando video {video_path}: {str(e)}")
            raise
        finally:
            self._processing_videos.pop(video_path_str, None)
    
    async def process_multiple_videos(self, video_paths: List[Path]) -> List[DetectionResult]:
        """Procesa múltiples videos de forma concurrente."""
        self.log_info(f"Iniciando procesamiento de {len(video_paths)} videos")
        
        # Validar todos los videos antes de procesarlos
        for video_path in video_paths:
            if not video_path.exists():
                raise FileNotFoundError(f"El archivo de video no existe: {video_path}")
            
            if not self.settings.is_supported_format(video_path):
                raise ValueError(f"Formato de video no soportado: {video_path.suffix}")
        
        # Crear tareas para procesamiento concurrente
        tasks = []
        for video_path in video_paths:
            task = asyncio.create_task(self.process_single_video(video_path))
            tasks.append(task)
        
        # Esperar a que todas las tareas se completen
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Separar resultados exitosos de errores
            successful_results = []
            errors = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_msg = f"Error procesando {video_paths[i]}: {str(result)}"
                    self.log_error(error_msg)
                    errors.append(error_msg)
                else:
                    successful_results.append(result)
            
            if errors:
                self.log_warning(f"Se completaron {len(successful_results)} videos exitosamente, {len(errors)} con errores")
            else:
                self.log_info(f"Todos los {len(successful_results)} videos procesados exitosamente")
            
            return successful_results
            
        except Exception as e:
            self.log_error(f"Error en procesamiento múltiple: {str(e)}")
            raise
    
    async def get_video_status(self, video_id: str) -> Optional[Video]:
        """Obtiene el estado de un video por su ID."""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self.process_video_use_case.video_repository.find_by_id,
                video_id
            )
        except Exception as e:
            self.log_error(f"Error obteniendo estado del video {video_id}: {str(e)}")
            return None
    
    async def get_detection_results(self, video_id: str) -> Optional[DetectionResult]:
        """Obtiene los resultados de detección para un video."""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self.get_detection_results_use_case.get_by_video_id,
                video_id
            )
        except Exception as e:
            self.log_error(f"Error obteniendo resultados de detección para video {video_id}: {str(e)}")
            return None
    
    async def get_all_videos(self) -> List[Video]:
        """Obtiene todos los videos registrados."""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self.process_video_use_case.video_repository.find_all
            )
        except Exception as e:
            self.log_error(f"Error obteniendo lista de videos: {str(e)}")
            return []
    
    async def get_videos_by_status(self, status: VideoStatus) -> List[Video]:
        """Obtiene videos filtrados por estado."""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self.process_video_use_case.video_repository.find_by_status,
                status
            )
        except Exception as e:
            self.log_error(f"Error obteniendo videos por estado {status}: {str(e)}")
            return []
    
    async def get_processing_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas de procesamiento."""
        try:
            stats = await asyncio.get_event_loop().run_in_executor(
                None,
                self.get_detection_results_use_case.get_statistics
            )
            
            # Agregar información de videos en procesamiento
            stats["currently_processing"] = len(self._processing_videos)
            stats["processing_videos"] = list(self._processing_videos.keys())
            
            return stats
            
        except Exception as e:
            self.log_error(f"Error obteniendo estadísticas: {str(e)}")
            return {
                "currently_processing": len(self._processing_videos),
                "processing_videos": list(self._processing_videos.keys()),
                "error": str(e)
            }
    
    def is_video_processing(self, video_path: Path) -> bool:
        """Verifica si un video está siendo procesado actualmente."""
        return str(video_path) in self._processing_videos
    
    def get_processing_queue_status(self) -> Dict[str, Any]:
        """Obtiene el estado de la cola de procesamiento."""
        return {
            "max_concurrent_processes": self.max_concurrent_processes,
            "currently_processing": len(self._processing_videos),
            "processing_videos": list(self._processing_videos.keys()),
            "available_slots": self.max_concurrent_processes - len(self._processing_videos)
        }
    
    async def cleanup_failed_videos(self) -> int:
        """Limpia videos que quedaron en estado de procesamiento después de un fallo."""
        try:
            failed_videos = await self.get_videos_by_status(VideoStatus.PROCESSING)
            count = 0
            
            for video in failed_videos:
                # Verificar si realmente no se está procesando
                if not self.is_video_processing(Path(video.file_path)):
                    video.status = VideoStatus.FAILED
                    video.updated_at = datetime.utcnow()
                    
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        self.process_video_use_case.video_repository.update,
                        video
                    )
                    count += 1
                    self.log_info(f"Video marcado como fallido: {video.file_path}")
            
            if count > 0:
                self.log_info(f"Se limpiaron {count} videos en estado inconsistente")
            
            return count
            
        except Exception as e:
            self.log_error(f"Error limpiando videos fallidos: {str(e)}")
            return 0
    
    def __del__(self):
        """Limpieza al destruir la instancia."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)