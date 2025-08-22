import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime
import uuid
import logging

from ...domain.entities.video import Video
from ...domain.entities.damage import Damage, DamageType, DamageSeverity, BoundingBox
from ...domain.entities.detection_result import DetectionResult, DetectionStatistics
from ...domain.services.damage_detection_service import DamageDetectionService


class YOLODamageDetector(DamageDetectionService):
    """Implementación del servicio de detección de daños usando YOLOv11."""
    
    def __init__(self, model_path: Optional[Path] = None, device: str = 'cpu'):
        self._model: Optional[YOLO] = None
        self._model_path = model_path
        self._device = device
        self._confidence_threshold = 0.5
        self._model_version = "YOLOv11"
        self._logger = logging.getLogger(__name__)
        
        # Mapeo de clases YOLO a tipos de daño
        self._class_mapping = {
            0: DamageType.SCRATCH,
            1: DamageType.DENT,
            2: DamageType.CRACK,
            3: DamageType.RUST,
            4: DamageType.BROKEN_PART
        }
        
        # Configuración de severidad basada en área y confianza
        self._severity_thresholds = {
            'area_small': 1000,    # píxeles
            'area_medium': 5000,   # píxeles
            'confidence_high': 0.8,
            'confidence_medium': 0.6
        }
    
    async def load_model(self, model_path: Optional[Path] = None) -> bool:
        """Carga el modelo YOLOv11."""
        try:
            if model_path:
                self._model_path = model_path
            
            # Si no se especifica un modelo, usar el modelo preentrenado de YOLO
            if self._model_path and self._model_path.exists():
                self._model = YOLO(str(self._model_path))
                self._logger.info(f"Modelo personalizado cargado desde: {self._model_path}")
            else:
                # Usar modelo preentrenado para detección de objetos
                self._model = YOLO('yolov8n.pt')  # Modelo ligero para empezar
                self._logger.info("Modelo YOLOv8n preentrenado cargado")
            
            # Configurar dispositivo
            if self._device == 'cuda' and not self._is_cuda_available():
                self._device = 'cpu'
                self._logger.warning("CUDA no disponible, usando CPU")
            
            self._model.to(self._device)
            self._logger.info(f"Modelo configurado para usar: {self._device}")
            
            return True
            
        except Exception as e:
            self._logger.error(f"Error al cargar el modelo: {e}")
            return False
    
    async def is_model_loaded(self) -> bool:
        """Verifica si el modelo está cargado."""
        return self._model is not None
    
    async def get_model_info(self) -> dict:
        """Obtiene información del modelo cargado."""
        if not self._model:
            return {"loaded": False}
        
        return {
            "loaded": True,
            "version": self._model_version,
            "device": self._device,
            "model_path": str(self._model_path) if self._model_path else "preentrenado",
            "confidence_threshold": self._confidence_threshold,
            "classes": list(self._class_mapping.values())
        }
    
    async def set_confidence_threshold(self, threshold: float) -> None:
        """Establece el umbral de confianza."""
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("El umbral de confianza debe estar entre 0.0 y 1.0")
        self._confidence_threshold = threshold
    
    async def get_supported_formats(self) -> List[str]:
        """Obtiene los formatos de video soportados."""
        return ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    
    async def detect_damages_in_video(self, video: Video, confidence_threshold: float = 0.5) -> DetectionResult:
        """Detecta daños en un video completo."""
        if not self._model:
            raise RuntimeError("El modelo no está cargado")
        
        await self.set_confidence_threshold(confidence_threshold)
        
        start_time = datetime.now()
        damages = []
        frames_processed = 0
        total_confidence = 0.0
        damages_by_type = {}
        damages_by_severity = {}
        
        try:
            # Abrir video con OpenCV
            cap = cv2.VideoCapture(str(video.file_path))
            if not cap.isOpened():
                raise ValueError(f"No se pudo abrir el video: {video.file_path}")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            frame_number = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Detectar daños en el frame actual
                frame_damages = await self.detect_damages_in_frame(
                    cv2.imencode('.jpg', frame)[1].tobytes(), 
                    frame_number
                )
                
                # Agregar timestamp a cada daño
                timestamp = frame_number / fps if fps > 0 else 0
                for damage in frame_damages:
                    damage.timestamp = timestamp
                    damages.append(damage)
                    
                    # Actualizar estadísticas
                    total_confidence += damage.confidence
                    
                    damage_type = damage.damage_type.value
                    damages_by_type[damage_type] = damages_by_type.get(damage_type, 0) + 1
                    
                    severity = damage.severity.value
                    damages_by_severity[severity] = damages_by_severity.get(severity, 0) + 1
                
                frames_processed += 1
                frame_number += 1
                
                # Log progreso cada 100 frames
                if frames_processed % 100 == 0:
                    self._logger.info(f"Procesados {frames_processed}/{total_frames} frames")
            
            cap.release()
            
        except Exception as e:
            self._logger.error(f"Error durante la detección: {e}")
            raise e
        
        # Calcular estadísticas finales
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        average_confidence = total_confidence / len(damages) if damages else 0.0
        fps_processed = frames_processed / processing_time if processing_time > 0 else 0.0
        
        statistics = DetectionStatistics(
            total_frames_processed=frames_processed,
            total_damages_detected=len(damages),
            damages_by_type=damages_by_type,
            damages_by_severity=damages_by_severity,
            average_confidence=average_confidence,
            processing_time=processing_time,
            frames_per_second=fps_processed
        )
        
        # Crear resultado de detección
        detection_result = DetectionResult(
            id=str(uuid.uuid4()),
            video=video,
            damages=damages,
            statistics=statistics,
            created_at=end_time,
            model_version=self._model_version,
            confidence_threshold=confidence_threshold
        )
        
        self._logger.info(f"Detección completada: {len(damages)} daños encontrados en {frames_processed} frames")
        
        return detection_result
    
    async def detect_damages_in_frame(self, frame_data: bytes, frame_number: int) -> List[Damage]:
        """Detecta daños en un frame específico."""
        if not self._model:
            raise RuntimeError("El modelo no está cargado")
        
        try:
            # Decodificar imagen desde bytes
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return []
            
            # Ejecutar detección
            results = self._model(frame, conf=self._confidence_threshold, verbose=False)
            
            damages = []
            
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        # Extraer información de la detección
                        confidence = float(box.conf.cpu().numpy()[0])
                        class_id = int(box.cls.cpu().numpy()[0])
                        
                        # Mapear clase a tipo de daño
                        damage_type = self._class_mapping.get(class_id, DamageType.UNKNOWN)
                        
                        # Obtener coordenadas del bounding box
                        x1, y1, x2, y2 = box.xyxy.cpu().numpy()[0]
                        
                        bounding_box = BoundingBox(
                            x1=float(x1),
                            y1=float(y1),
                            x2=float(x2),
                            y2=float(y2)
                        )
                        
                        # Determinar severidad
                        severity = self._determine_severity(bounding_box, confidence)
                        
                        # Crear entidad Damage
                        damage = Damage(
                            id=str(uuid.uuid4()),
                            damage_type=damage_type,
                            severity=severity,
                            confidence=confidence,
                            bounding_box=bounding_box,
                            frame_number=frame_number,
                            timestamp=0.0  # Se establecerá en detect_damages_in_video
                        )
                        
                        damages.append(damage)
            
            return damages
            
        except Exception as e:
            self._logger.error(f"Error en detección de frame {frame_number}: {e}")
            return []
    
    def _determine_severity(self, bounding_box: BoundingBox, confidence: float) -> DamageSeverity:
        """Determina la severidad del daño basado en el área y confianza."""
        area = bounding_box.area
        
        # Severidad basada en confianza alta
        if confidence >= self._severity_thresholds['confidence_high']:
            if area >= self._severity_thresholds['area_medium']:
                return DamageSeverity.CRITICAL
            elif area >= self._severity_thresholds['area_small']:
                return DamageSeverity.SEVERE
            else:
                return DamageSeverity.MODERATE
        
        # Severidad basada en confianza media
        elif confidence >= self._severity_thresholds['confidence_medium']:
            if area >= self._severity_thresholds['area_medium']:
                return DamageSeverity.SEVERE
            elif area >= self._severity_thresholds['area_small']:
                return DamageSeverity.MODERATE
            else:
                return DamageSeverity.MINOR
        
        # Confianza baja
        else:
            if area >= self._severity_thresholds['area_medium']:
                return DamageSeverity.MODERATE
            else:
                return DamageSeverity.MINOR
    
    def _is_cuda_available(self) -> bool:
        """Verifica si CUDA está disponible."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False