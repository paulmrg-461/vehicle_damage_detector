from typing import Optional
from pathlib import Path
from datetime import datetime
import uuid

from ..entities.video import Video, VideoStatus
from ..entities.detection_result import DetectionResult
from ..repositories.video_repository import VideoRepository
from ..repositories.detection_repository import DetectionRepository
from ..services.damage_detection_service import DamageDetectionService
from ..services.video_processing_service import VideoProcessingService


class ProcessVideoUseCase:
    """Caso de uso para procesar un video y detectar daños."""
    
    def __init__(
        self,
        video_repository: VideoRepository,
        detection_repository: DetectionRepository,
        damage_detection_service: DamageDetectionService,
        video_processing_service: VideoProcessingService
    ):
        self._video_repository = video_repository
        self._detection_repository = detection_repository
        self._damage_detection_service = damage_detection_service
        self._video_processing_service = video_processing_service
    
    async def execute(
        self, 
        video_path: Path, 
        confidence_threshold: float = 0.5,
        create_annotated_video: bool = True
    ) -> DetectionResult:
        """Ejecuta el procesamiento completo de un video."""
        
        # Validar que el archivo existe
        if not video_path.exists():
            raise FileNotFoundError(f"El archivo de video no existe: {video_path}")
        
        # Validar que el video es procesable
        is_valid = await self._video_processing_service.validate_video(video_path)
        if not is_valid:
            raise ValueError(f"El archivo no es un video válido: {video_path}")
        
        # Verificar si el modelo está cargado
        if not await self._damage_detection_service.is_model_loaded():
            await self._damage_detection_service.load_model()
        
        # Extraer metadatos del video
        metadata = await self._video_processing_service.extract_metadata(video_path)
        
        # Crear entidad Video
        video = Video(
            id=str(uuid.uuid4()),
            name=video_path.name,
            file_path=video_path,
            status=VideoStatus.PROCESSING,
            created_at=datetime.now(),
            metadata=metadata
        )
        
        try:
            # Guardar video en repositorio
            video = await self._video_repository.save(video)
            
            # Configurar umbral de confianza
            await self._damage_detection_service.set_confidence_threshold(confidence_threshold)
            
            # Detectar daños en el video
            detection_result = await self._damage_detection_service.detect_damages_in_video(
                video, confidence_threshold
            )
            
            # Crear video anotado si se solicita
            if create_annotated_video and detection_result.has_damages:
                output_dir = video_path.parent / "output"
                output_dir.mkdir(exist_ok=True)
                
                annotated_path = output_dir / f"annotated_{video_path.name}"
                annotated_video_path = await self._video_processing_service.create_annotated_video(
                    video, detection_result, annotated_path
                )
                detection_result.annotated_video_path = annotated_video_path
            
            # Actualizar estado del video
            video.status = VideoStatus.COMPLETED
            video.damages = detection_result.damages
            await self._video_repository.update(video)
            
            # Guardar resultado de detección
            detection_result = await self._detection_repository.save(detection_result)
            
            return detection_result
            
        except Exception as e:
            # Actualizar estado del video en caso de error
            video.status = VideoStatus.FAILED
            await self._video_repository.update(video)
            raise e
    
    async def get_processing_status(self, video_id: str) -> Optional[str]:
        """Obtiene el estado de procesamiento de un video."""
        video = await self._video_repository.find_by_id(video_id)
        return video.status.value if video else None
    
    async def cancel_processing(self, video_id: str) -> bool:
        """Cancela el procesamiento de un video."""
        video = await self._video_repository.find_by_id(video_id)
        if video and video.status == VideoStatus.PROCESSING:
            video.status = VideoStatus.CANCELLED
            await self._video_repository.update(video)
            return True
        return False