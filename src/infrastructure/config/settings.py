from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "protected_namespaces": ('settings_',)
    }
    
    # Configuración general
    app_name: str = Field(default="Vehicle Damage Detector", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Configuración del servidor
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=False, env="RELOAD")
    
    # Configuración de rutas
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent.parent)
    videos_dir: Path = Field(default_factory=lambda: Path("videos"))
    output_dir: Path = Field(default_factory=lambda: Path("output"))
    logs_dir: Path = Field(default_factory=lambda: Path("logs"))
    models_dir: Path = Field(default_factory=lambda: Path("models"))
    config_dir: Path = Field(default_factory=lambda: Path("config"))
    
    # Configuración de almacenamiento
    storage_type: str = Field(default="json", env="STORAGE_TYPE")
    storage_path: Path = Field(default_factory=lambda: Path("data"))
    
    # Configuración del modelo YOLO
    model_path: Optional[Path] = Field(default=None, env="MODEL_PATH")
    model_device: str = Field(default="cpu", env="MODEL_DEVICE")
    confidence_threshold: float = Field(default=0.5, env="CONFIDENCE_THRESHOLD")
    
    # Configuración de procesamiento de video
    max_video_size_mb: int = Field(default=500, env="MAX_VIDEO_SIZE_MB")
    supported_formats: List[str] = Field(
        default=[".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"],
        env="SUPPORTED_FORMATS"
    )
    frame_extraction_interval: int = Field(default=1, env="FRAME_EXTRACTION_INTERVAL")
    create_annotated_videos: bool = Field(default=True, env="CREATE_ANNOTATED_VIDEOS")
    
    # Configuración de logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        env="LOG_FORMAT"
    )
    log_rotation: str = Field(default="1 day", env="LOG_ROTATION")
    log_retention: str = Field(default="30 days", env="LOG_RETENTION")
    
    # Configuración de API
    api_title: str = Field(default="Vehicle Damage Detection API", env="API_TITLE")
    api_description: str = Field(
        default="API para detección de daños en vehículos usando YOLOv11",
        env="API_DESCRIPTION"
    )
    api_version: str = Field(default="1.0.0", env="API_VERSION")
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # Configuración de seguridad
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Configuración de límites
    max_concurrent_detections: int = Field(default=2, env="MAX_CONCURRENT_DETECTIONS")
    request_timeout_seconds: int = Field(default=300, env="REQUEST_TIMEOUT_SECONDS")
    

    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_directories()
    
    def _setup_directories(self):
        """Configura las rutas absolutas de los directorios."""
        if not self.videos_dir.is_absolute():
            self.videos_dir = self.base_dir / self.videos_dir
        
        if not self.output_dir.is_absolute():
            self.output_dir = self.base_dir / self.output_dir
        
        if not self.logs_dir.is_absolute():
            self.logs_dir = self.base_dir / self.logs_dir
        
        if not self.models_dir.is_absolute():
            self.models_dir = self.base_dir / self.models_dir
        
        if not self.config_dir.is_absolute():
            self.config_dir = self.base_dir / self.config_dir
        
        if not self.storage_path.is_absolute():
            self.storage_path = self.base_dir / self.storage_path
        
        # Crear directorios si no existen
        for directory in [self.videos_dir, self.output_dir, self.logs_dir, 
                         self.models_dir, self.config_dir, self.storage_path]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def database_url(self) -> str:
        """URL de la base de datos (para futuras implementaciones)."""
        return f"sqlite:///{self.storage_path}/app.db"
    
    @property
    def log_file_path(self) -> Path:
        """Ruta del archivo de log."""
        return self.logs_dir / "app.log"
    
    @property
    def max_video_size_bytes(self) -> int:
        """Tamaño máximo de video en bytes."""
        return self.max_video_size_mb * 1024 * 1024
    
    def get_model_path(self) -> Optional[Path]:
        """Obtiene la ruta del modelo, buscando en el directorio de modelos si es necesario."""
        if self.model_path:
            if self.model_path.is_absolute():
                return self.model_path
            else:
                return self.models_dir / self.model_path
        return None
    
    def is_supported_format(self, file_path: Path) -> bool:
        """Verifica si el formato del archivo es soportado."""
        return file_path.suffix.lower() in self.supported_formats
    
    def get_output_path(self, filename: str) -> Path:
        """Genera una ruta de salida para un archivo."""
        return self.output_dir / filename
    
    def get_annotated_video_path(self, original_path: Path) -> Path:
        """Genera la ruta para un video anotado."""
        stem = original_path.stem
        suffix = original_path.suffix
        return self.output_dir / f"annotated_{stem}{suffix}"
    
    def get_thumbnail_path(self, video_id: str) -> Path:
        """Genera la ruta para una miniatura."""
        return self.output_dir / f"thumbnail_{video_id}.jpg"


# Instancia global de configuración
settings = Settings()


def get_settings() -> Settings:
    """Función para obtener la configuración (útil para inyección de dependencias)."""
    return settings