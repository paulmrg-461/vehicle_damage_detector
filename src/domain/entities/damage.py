from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime
from enum import Enum


class DamageType(Enum):
    """Tipos de daños que se pueden detectar en vehículos."""
    SCRATCH = "scratch"  # Rayón/arañazo en la pintura
    DENT = "dent"        # Abolladura
    CRACK = "crack"      # Grieta
    RUST = "rust"        # Óxido
    BROKEN_PART = "broken_part"  # Parte rota
    UNKNOWN = "unknown"   # Daño no clasificado


class DamageSeverity(Enum):
    """Niveles de severidad del daño."""
    LOW = "low"          # Daño menor
    MEDIUM = "medium"    # Daño moderado
    HIGH = "high"        # Daño severo
    CRITICAL = "critical" # Daño crítico


@dataclass
class BoundingBox:
    """Representa las coordenadas de un bounding box."""
    x: float
    y: float
    width: float
    height: float
    
    def __post_init__(self):
        """Validar que las coordenadas sean válidas."""
        if self.x < 0 or self.y < 0:
            raise ValueError("Las coordenadas x e y deben ser positivas")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("El ancho y alto deben ser positivos")
    
    @property
    def area(self) -> float:
        """Calcula el área del bounding box."""
        return self.width * self.height
    
    @property
    def center(self) -> Tuple[float, float]:
        """Obtiene el centro del bounding box."""
        return (self.x + self.width / 2, self.y + self.height / 2)


@dataclass
class Damage:
    """Entidad que representa un daño detectado en un vehículo."""
    id: str
    damage_type: DamageType
    severity: DamageSeverity
    confidence: float
    bounding_box: BoundingBox
    frame_number: int
    timestamp: datetime
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validar los datos del daño."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("La confianza debe estar entre 0.0 y 1.0")
        if self.frame_number < 0:
            raise ValueError("El número de frame debe ser positivo")
    
    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        """Determina si el daño tiene alta confianza."""
        return self.confidence >= threshold
    
    def is_severe(self) -> bool:
        """Determina si el daño es severo o crítico."""
        return self.severity in [DamageSeverity.HIGH, DamageSeverity.CRITICAL]
    
    def to_dict(self) -> dict:
        """Convierte el daño a diccionario para serialización."""
        return {
            "id": self.id,
            "damage_type": self.damage_type.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "bounding_box": {
                "x": self.bounding_box.x,
                "y": self.bounding_box.y,
                "width": self.bounding_box.width,
                "height": self.bounding_box.height
            },
            "frame_number": self.frame_number,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description
        }