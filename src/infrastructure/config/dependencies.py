from functools import lru_cache
from typing import Dict, Any

from src.domain.repositories.video_repository import VideoRepository
from src.domain.repositories.detection_repository import DetectionRepository
from src.domain.services.damage_detection_service import DamageDetectionService
from src.domain.services.video_processing_service import VideoProcessingService
from src.domain.use_cases.process_video_use_case import ProcessVideoUseCase
from src.domain.use_cases.get_detection_results_use_case import GetDetectionResultsUseCase
from src.application.services.video_processing_app_service import VideoProcessingAppService

from src.infrastructure.repositories.json_video_repository import JsonVideoRepository
from src.infrastructure.repositories.json_detection_repository import JsonDetectionRepository
from src.infrastructure.ml.yolo_damage_detector import YOLODamageDetector
from src.infrastructure.video.opencv_video_processor import OpenCVVideoProcessor
from src.infrastructure.config.settings import get_settings
from src.infrastructure.config.logging_config import get_logger


class DependencyContainer:
    """Contenedor de dependencias para inyección de dependencias."""
    
    def __init__(self):
        self._instances: Dict[str, Any] = {}
        self._settings = get_settings()
        self._logger = get_logger("DependencyContainer")
        self._logger.info("Inicializando contenedor de dependencias")
    
    @lru_cache(maxsize=1)
    def get_video_repository(self) -> VideoRepository:
        """Obtiene la instancia del repositorio de videos."""
        if "video_repository" not in self._instances:
            storage_path = self._settings.storage_path / "videos.json"
            self._instances["video_repository"] = JsonVideoRepository(storage_path)
            self._logger.info(f"VideoRepository creado con storage: {storage_path}")
        return self._instances["video_repository"]
    
    @lru_cache(maxsize=1)
    def get_detection_repository(self) -> DetectionRepository:
        """Obtiene la instancia del repositorio de detecciones."""
        if "detection_repository" not in self._instances:
            storage_path = self._settings.storage_path / "detections.json"
            self._instances["detection_repository"] = JsonDetectionRepository(storage_path)
            self._logger.info(f"DetectionRepository creado con storage: {storage_path}")
        return self._instances["detection_repository"]
    
    @lru_cache(maxsize=1)
    def get_damage_detection_service(self) -> DamageDetectionService:
        """Obtiene la instancia del servicio de detección de daños."""
        if "damage_detection_service" not in self._instances:
            # Usar el archivo específico del modelo en lugar del directorio
            model_path = self._settings.models_dir / "yolov8n.pt"
            device = self._settings.model_device
            confidence_threshold = self._settings.confidence_threshold
            
            self._instances["damage_detection_service"] = YOLODamageDetector(
                model_path=model_path,
                device=device
            )
            self._logger.info(f"DamageDetectionService creado - Modelo: {model_path}, Device: {device}")
        return self._instances["damage_detection_service"]
    
    @lru_cache(maxsize=1)
    def get_video_processing_service(self) -> VideoProcessingService:
        """Obtiene la instancia del servicio de procesamiento de video."""
        if "video_processing_service" not in self._instances:
            output_dir = self._settings.output_dir
            supported_formats = self._settings.supported_formats
            
            self._instances["video_processing_service"] = OpenCVVideoProcessor()
            self._logger.info(f"VideoProcessingService creado - Output: {output_dir}")
        return self._instances["video_processing_service"]
    
    @lru_cache(maxsize=1)
    def get_process_video_use_case(self) -> ProcessVideoUseCase:
        """Obtiene la instancia del caso de uso de procesamiento de video."""
        if "process_video_use_case" not in self._instances:
            video_repo = self.get_video_repository()
            detection_repo = self.get_detection_repository()
            damage_service = self.get_damage_detection_service()
            video_service = self.get_video_processing_service()
            
            self._instances["process_video_use_case"] = ProcessVideoUseCase(
                video_repository=video_repo,
                detection_repository=detection_repo,
                damage_detection_service=damage_service,
                video_processing_service=video_service
            )
            self._logger.info("ProcessVideoUseCase creado")
        return self._instances["process_video_use_case"]
    
    @lru_cache(maxsize=1)
    def get_detection_results_use_case(self) -> GetDetectionResultsUseCase:
        """Obtiene la instancia del caso de uso de obtención de resultados."""
        if "detection_results_use_case" not in self._instances:
            detection_repo = self.get_detection_repository()
            video_repo = self.get_video_repository()
            
            self._instances["detection_results_use_case"] = GetDetectionResultsUseCase(
                detection_repository=detection_repo,
                video_repository=video_repo
            )
            self._logger.info("GetDetectionResultsUseCase creado")
        return self._instances["detection_results_use_case"]
    
    @lru_cache(maxsize=1)
    def get_video_processing_app_service(self) -> VideoProcessingAppService:
        """Obtiene la instancia del servicio de aplicación de procesamiento de video."""
        if "video_processing_app_service" not in self._instances:
            process_video_use_case = self.get_process_video_use_case()
            detection_results_use_case = self.get_detection_results_use_case()
            
            self._instances["video_processing_app_service"] = VideoProcessingAppService(
                process_video_use_case=process_video_use_case,
                get_detection_results_use_case=detection_results_use_case
            )
            self._logger.info("VideoProcessingAppService creado")
        return self._instances["video_processing_app_service"]
    
    def clear_cache(self):
        """Limpia el cache de instancias."""
        self._instances.clear()
        # Limpiar cache de lru_cache
        self.get_video_repository.cache_clear()
        self.get_detection_repository.cache_clear()
        self.get_damage_detection_service.cache_clear()
        self.get_video_processing_service.cache_clear()
        self.get_process_video_use_case.cache_clear()
        self.get_detection_results_use_case.cache_clear()
        self.get_video_processing_app_service.cache_clear()
        self._logger.info("Cache de dependencias limpiado")
    
    def get_settings(self):
        """Obtiene la configuración de la aplicación."""
        return self._settings
    
    async def health_check(self) -> Dict[str, bool]:
        """Verifica el estado de salud de las dependencias."""
        health_status = {}
        
        try:
            # Verificar repositorios
            video_repo = self.get_video_repository()
            health_status["video_repository"] = True
        except Exception as e:
            self._logger.error(f"Error en video_repository: {e}")
            health_status["video_repository"] = False
        
        try:
            detection_repo = self.get_detection_repository()
            health_status["detection_repository"] = True
        except Exception as e:
            self._logger.error(f"Error en detection_repository: {e}")
            health_status["detection_repository"] = False
        
        try:
            # Verificar servicios
            damage_service = self.get_damage_detection_service()
            health_status["damage_detection_service"] = await damage_service.is_model_loaded()
        except Exception as e:
            self._logger.error(f"Error en damage_detection_service: {e}")
            health_status["damage_detection_service"] = False
        
        try:
            video_service = self.get_video_processing_service()
            health_status["video_processing_service"] = True
        except Exception as e:
            self._logger.error(f"Error en video_processing_service: {e}")
            health_status["video_processing_service"] = False
        
        return health_status


# Instancia global del contenedor de dependencias
_container: DependencyContainer = None


def get_container() -> DependencyContainer:
    """Obtiene la instancia global del contenedor de dependencias."""
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container


# Funciones de conveniencia para FastAPI dependency injection
def get_video_repository() -> VideoRepository:
    """Dependency injection para VideoRepository."""
    return get_container().get_video_repository()


def get_detection_repository() -> DetectionRepository:
    """Dependency injection para DetectionRepository."""
    return get_container().get_detection_repository()


def get_damage_detection_service() -> DamageDetectionService:
    """Dependency injection para DamageDetectionService."""
    return get_container().get_damage_detection_service()


def get_video_processing_service() -> VideoProcessingService:
    """Dependency injection para VideoProcessingService."""
    return get_container().get_video_processing_service()


def get_process_video_use_case() -> ProcessVideoUseCase:
    """Dependency injection para ProcessVideoUseCase."""
    return get_container().get_process_video_use_case()


def get_detection_results_use_case() -> GetDetectionResultsUseCase:
    """Dependency injection para GetDetectionResultsUseCase."""
    return get_container().get_detection_results_use_case()


def reset_dependencies():
    """Reinicia todas las dependencias (útil para testing)."""
    global _container
    if _container:
        _container.clear_cache()
    _container = None