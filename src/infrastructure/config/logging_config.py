from loguru import logger
from pathlib import Path
from typing import Dict, Any
import sys

from .settings import get_settings


def setup_logging() -> None:
    """Configura el sistema de logging usando Loguru."""
    settings = get_settings()
    
    # Remover el handler por defecto de loguru
    logger.remove()
    
    # Configurar formato de log
    log_format = settings.log_format
    
    # Handler para consola
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Handler para archivo
    logger.add(
        settings.log_file_path,
        format=log_format,
        level=settings.log_level,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Handler para errores críticos (archivo separado)
    error_log_path = settings.logs_dir / "errors.log"
    logger.add(
        error_log_path,
        format=log_format,
        level="ERROR",
        rotation="1 week",
        retention="60 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    logger.info(f"Logging configurado - Nivel: {settings.log_level}")
    logger.info(f"Archivo de log: {settings.log_file_path}")
    logger.info(f"Archivo de errores: {error_log_path}")


def get_logger(name: str = None):
    """Obtiene un logger con el nombre especificado."""
    if name:
        return logger.bind(name=name)
    return logger


def log_function_call(func_name: str, **kwargs):
    """Decorator para loggear llamadas a funciones."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"Llamando función: {func_name} con args: {args}, kwargs: {kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Función {func_name} completada exitosamente")
                return result
            except Exception as e:
                logger.error(f"Error en función {func_name}: {str(e)}")
                raise
        return wrapper
    return decorator


def log_processing_step(step_name: str, video_id: str = None):
    """Decorator para loggear pasos de procesamiento."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            video_info = f" (Video: {video_id})" if video_id else ""
            logger.info(f"Iniciando paso: {step_name}{video_info}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"Paso completado: {step_name}{video_info}")
                return result
            except Exception as e:
                logger.error(f"Error en paso {step_name}{video_info}: {str(e)}")
                raise
        return wrapper
    return decorator


class LoggerMixin:
    """Mixin para agregar capacidades de logging a las clases."""
    
    @property
    def logger(self):
        """Obtiene un logger para la clase actual."""
        return get_logger(self.__class__.__name__)
    
    def log_info(self, message: str, **kwargs):
        """Log de información."""
        self.logger.info(message, **kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log de debug."""
        self.logger.debug(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log de advertencia."""
        self.logger.warning(message, **kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log de error."""
        self.logger.error(message, **kwargs)
    
    def log_exception(self, message: str, **kwargs):
        """Log de excepción con traceback."""
        self.logger.exception(message, **kwargs)


# Configuración específica para diferentes módulos
LOGGING_CONFIG: Dict[str, Any] = {
    "loggers": {
        "yolo_damage_detector": {
            "level": "INFO",
            "handlers": ["console", "file"]
        },
        "opencv_video_processor": {
            "level": "INFO", 
            "handlers": ["console", "file"]
        },
        "process_video_use_case": {
            "level": "INFO",
            "handlers": ["console", "file"]
        },
        "api": {
            "level": "INFO",
            "handlers": ["console", "file"]
        }
    }
}


def configure_module_logger(module_name: str, level: str = None):
    """Configura un logger específico para un módulo."""
    config = LOGGING_CONFIG["loggers"].get(module_name, {})
    log_level = level or config.get("level", "INFO")
    
    module_logger = get_logger(module_name)
    module_logger.info(f"Logger configurado para módulo: {module_name} - Nivel: {log_level}")
    
    return module_logger