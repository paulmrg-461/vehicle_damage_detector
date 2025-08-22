from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from .damage import Damage
from .video import Video


@dataclass
class DetectionStatistics:
    """Estadísticas de la detección de daños."""
    total_frames_processed: int
    total_damages_detected: int
    damages_by_type: Dict[str, int]
    damages_by_severity: Dict[str, int]
    average_confidence: float
    processing_time: float
    frames_per_second: float
    
    def __post_init__(self):
        """Validar estadísticas."""
        if self.total_frames_processed < 0:
            raise ValueError("El total de frames procesados debe ser positivo")
        if self.total_damages_detected < 0:
            raise ValueError("El total de daños detectados debe ser positivo")
        if not 0.0 <= self.average_confidence <= 1.0:
            raise ValueError("La confianza promedio debe estar entre 0.0 y 1.0")
        if self.processing_time < 0:
            raise ValueError("El tiempo de procesamiento debe ser positivo")
        if self.frames_per_second < 0:
            raise ValueError("Los frames por segundo deben ser positivos")


@dataclass
class DetectionResult:
    """Resultado completo de la detección de daños en un video."""
    id: str
    video: Video
    damages: List[Damage]
    statistics: DetectionStatistics
    created_at: datetime
    model_version: str
    confidence_threshold: float
    output_path: Optional[Path] = None
    annotated_video_path: Optional[Path] = None
    
    def __post_init__(self):
        """Validar resultado de detección."""
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError("El umbral de confianza debe estar entre 0.0 y 1.0")
        if not self.model_version:
            raise ValueError("La versión del modelo es requerida")
    
    @property
    def has_damages(self) -> bool:
        """Verifica si se detectaron daños."""
        return len(self.damages) > 0
    
    @property
    def damage_count(self) -> int:
        """Obtiene el número total de daños detectados."""
        return len(self.damages)
    
    @property
    def high_confidence_damages(self) -> List[Damage]:
        """Obtiene daños con confianza superior al umbral."""
        return [damage for damage in self.damages if damage.confidence >= self.confidence_threshold]
    
    @property
    def severe_damages(self) -> List[Damage]:
        """Obtiene daños severos o críticos."""
        return [damage for damage in self.damages if damage.is_severe()]
    
    @property
    def unique_damage_types(self) -> List[str]:
        """Obtiene los tipos únicos de daños detectados."""
        return list(set(damage.damage_type.value for damage in self.damages))
    
    def get_damages_by_frame(self, frame_number: int) -> List[Damage]:
        """Obtiene todos los daños detectados en un frame específico."""
        return [damage for damage in self.damages if damage.frame_number == frame_number]
    
    def get_damages_by_type(self, damage_type: str) -> List[Damage]:
        """Obtiene todos los daños de un tipo específico."""
        return [damage for damage in self.damages if damage.damage_type.value == damage_type]
    
    def get_damages_by_confidence_range(self, min_confidence: float, max_confidence: float = 1.0) -> List[Damage]:
        """Obtiene daños dentro de un rango de confianza."""
        return [
            damage for damage in self.damages 
            if min_confidence <= damage.confidence <= max_confidence
        ]
    
    def calculate_damage_density(self) -> float:
        """Calcula la densidad de daños por frame."""
        if self.statistics.total_frames_processed == 0:
            return 0.0
        return self.damage_count / self.statistics.total_frames_processed
    
    def generate_summary(self) -> Dict[str, any]:
        """Genera un resumen del resultado de detección."""
        return {
            "video_name": self.video.name,
            "total_damages": self.damage_count,
            "high_confidence_damages": len(self.high_confidence_damages),
            "severe_damages": len(self.severe_damages),
            "unique_damage_types": self.unique_damage_types,
            "damage_density": self.calculate_damage_density(),
            "processing_time": self.statistics.processing_time,
            "average_confidence": self.statistics.average_confidence,
            "frames_processed": self.statistics.total_frames_processed,
            "model_version": self.model_version,
            "confidence_threshold": self.confidence_threshold
        }
    
    def to_dict(self) -> dict:
        """Convierte el resultado a diccionario para serialización."""
        return {
            "id": self.id,
            "video": self.video.to_dict(),
            "damages": [damage.to_dict() for damage in self.damages],
            "statistics": {
                "total_frames_processed": self.statistics.total_frames_processed,
                "total_damages_detected": self.statistics.total_damages_detected,
                "damages_by_type": self.statistics.damages_by_type,
                "damages_by_severity": self.statistics.damages_by_severity,
                "average_confidence": self.statistics.average_confidence,
                "processing_time": self.statistics.processing_time,
                "frames_per_second": self.statistics.frames_per_second
            },
            "created_at": self.created_at.isoformat(),
            "model_version": self.model_version,
            "confidence_threshold": self.confidence_threshold,
            "output_path": str(self.output_path) if self.output_path else None,
            "annotated_video_path": str(self.annotated_video_path) if self.annotated_video_path else None,
            "summary": self.generate_summary()
        }