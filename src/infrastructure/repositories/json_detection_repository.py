import json
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import logging

from ...domain.entities.detection_result import DetectionResult, DetectionStatistics
from ...domain.entities.damage import Damage, DamageType, DamageSeverity, BoundingBox
from ...domain.entities.video import Video, VideoStatus, VideoFormat, VideoMetadata
from ...domain.repositories.detection_repository import DetectionRepository


class JsonDetectionRepository(DetectionRepository):
    """Implementación del repositorio de detecciones usando archivos JSON."""
    
    def __init__(self, storage_path: Path):
        self._storage_path = storage_path
        self._detections_file = storage_path / "detections.json"
        self._logger = logging.getLogger(__name__)
        
        # Asegurar que el directorio existe
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Inicializar archivo si no existe
        if not self._detections_file.exists():
            self._save_data({})
    
    async def save(self, detection_result: DetectionResult) -> DetectionResult:
        """Guarda un resultado de detección."""
        try:
            data = await self._load_data()
            data[detection_result.id] = self._detection_to_dict(detection_result)
            await self._save_data(data)
            
            self._logger.info(f"Resultado de detección guardado: {detection_result.id}")
            return detection_result
            
        except Exception as e:
            self._logger.error(f"Error al guardar detección {detection_result.id}: {e}")
            raise e
    
    async def find_by_id(self, result_id: str) -> Optional[DetectionResult]:
        """Busca un resultado por su ID."""
        try:
            data = await self._load_data()
            detection_data = data.get(result_id)
            
            if detection_data:
                return self._dict_to_detection(detection_data)
            return None
            
        except Exception as e:
            self._logger.error(f"Error al buscar detección {result_id}: {e}")
            return None
    
    async def find_by_video_id(self, video_id: str) -> List[DetectionResult]:
        """Busca resultados por ID de video."""
        try:
            data = await self._load_data()
            results = []
            
            for detection_data in data.values():
                if detection_data['video']['id'] == video_id:
                    result = self._dict_to_detection(detection_data)
                    results.append(result)
            
            return results
            
        except Exception as e:
            self._logger.error(f"Error al buscar detecciones por video {video_id}: {e}")
            return []
    
    async def find_all(self) -> List[DetectionResult]:
        """Obtiene todos los resultados de detección."""
        try:
            data = await self._load_data()
            results = []
            
            for detection_data in data.values():
                result = self._dict_to_detection(detection_data)
                results.append(result)
            
            return results
            
        except Exception as e:
            self._logger.error(f"Error al obtener todas las detecciones: {e}")
            return []
    
    async def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[DetectionResult]:
        """Busca resultados en un rango de fechas."""
        try:
            data = await self._load_data()
            results = []
            
            for detection_data in data.values():
                created_at = datetime.fromisoformat(detection_data['created_at'])
                if start_date <= created_at <= end_date:
                    result = self._dict_to_detection(detection_data)
                    results.append(result)
            
            return results
            
        except Exception as e:
            self._logger.error(f"Error al buscar detecciones por rango de fechas: {e}")
            return []
    
    async def find_with_damages(self) -> List[DetectionResult]:
        """Busca resultados que contengan daños detectados."""
        try:
            data = await self._load_data()
            results = []
            
            for detection_data in data.values():
                if detection_data['damages']:  # Si tiene daños
                    result = self._dict_to_detection(detection_data)
                    results.append(result)
            
            return results
            
        except Exception as e:
            self._logger.error(f"Error al buscar detecciones con daños: {e}")
            return []
    
    async def find_by_damage_type(self, damage_type: str) -> List[DetectionResult]:
        """Busca resultados que contengan un tipo específico de daño."""
        try:
            data = await self._load_data()
            results = []
            
            for detection_data in data.values():
                # Verificar si algún daño coincide con el tipo
                has_damage_type = any(
                    damage['damage_type'] == damage_type 
                    for damage in detection_data['damages']
                )
                
                if has_damage_type:
                    result = self._dict_to_detection(detection_data)
                    results.append(result)
            
            return results
            
        except Exception as e:
            self._logger.error(f"Error al buscar detecciones por tipo de daño {damage_type}: {e}")
            return []
    
    async def update(self, detection_result: DetectionResult) -> DetectionResult:
        """Actualiza un resultado de detección."""
        try:
            data = await self._load_data()
            
            if detection_result.id not in data:
                raise ValueError(f"Resultado de detección no encontrado: {detection_result.id}")
            
            data[detection_result.id] = self._detection_to_dict(detection_result)
            await self._save_data(data)
            
            self._logger.info(f"Resultado de detección actualizado: {detection_result.id}")
            return detection_result
            
        except Exception as e:
            self._logger.error(f"Error al actualizar detección {detection_result.id}: {e}")
            raise e
    
    async def delete(self, result_id: str) -> bool:
        """Elimina un resultado de detección."""
        try:
            data = await self._load_data()
            
            if result_id in data:
                del data[result_id]
                await self._save_data(data)
                self._logger.info(f"Resultado de detección eliminado: {result_id}")
                return True
            
            return False
            
        except Exception as e:
            self._logger.error(f"Error al eliminar detección {result_id}: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, any]:
        """Obtiene estadísticas generales de detecciones."""
        try:
            data = await self._load_data()
            
            total_detections = len(data)
            total_damages = 0
            total_processing_time = 0.0
            damages_by_type = {}
            damages_by_severity = {}
            
            for detection_data in data.values():
                damages = detection_data['damages']
                total_damages += len(damages)
                total_processing_time += detection_data['statistics']['processing_time']
                
                # Contar por tipo y severidad
                for damage in damages:
                    damage_type = damage['damage_type']
                    severity = damage['severity']
                    
                    damages_by_type[damage_type] = damages_by_type.get(damage_type, 0) + 1
                    damages_by_severity[severity] = damages_by_severity.get(severity, 0) + 1
            
            return {
                'total_detections': total_detections,
                'total_damages': total_damages,
                'average_damages_per_detection': total_damages / total_detections if total_detections > 0 else 0,
                'total_processing_time': total_processing_time,
                'average_processing_time': total_processing_time / total_detections if total_detections > 0 else 0,
                'damages_by_type': damages_by_type,
                'damages_by_severity': damages_by_severity
            }
            
        except Exception as e:
            self._logger.error(f"Error al obtener estadísticas: {e}")
            return {}
    
    async def exists(self, result_id: str) -> bool:
        """Verifica si existe un resultado con el ID dado."""
        try:
            data = await self._load_data()
            return result_id in data
            
        except Exception as e:
            self._logger.error(f"Error al verificar existencia de detección {result_id}: {e}")
            return False
    
    async def _load_data(self) -> Dict[str, Any]:
        """Carga datos del archivo JSON."""
        try:
            with open(self._detections_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    async def _save_data(self, data: Dict[str, Any]) -> None:
        """Guarda datos en el archivo JSON."""
        with open(self._detections_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def _detection_to_dict(self, detection: DetectionResult) -> Dict[str, Any]:
        """Convierte un DetectionResult a diccionario."""
        return {
            'id': detection.id,
            'video': {
                'id': detection.video.id,
                'name': detection.video.name,
                'file_path': str(detection.video.file_path),
                'status': detection.video.status.value,
                'created_at': detection.video.created_at.isoformat(),
                'metadata': {
                    'duration': detection.video.metadata.duration,
                    'fps': detection.video.metadata.fps,
                    'width': detection.video.metadata.width,
                    'height': detection.video.metadata.height,
                    'frame_count': detection.video.metadata.frame_count,
                    'file_size': detection.video.metadata.file_size,
                    'format': detection.video.metadata.format.value,
                    'codec': detection.video.metadata.codec,
                    'bitrate': detection.video.metadata.bitrate
                } if detection.video.metadata else None
            },
            'damages': [
                {
                    'id': damage.id,
                    'damage_type': damage.damage_type.value,
                    'severity': damage.severity.value,
                    'confidence': damage.confidence,
                    'bounding_box': {
                        'x1': damage.bounding_box.x1,
                        'y1': damage.bounding_box.y1,
                        'x2': damage.bounding_box.x2,
                        'y2': damage.bounding_box.y2
                    },
                    'frame_number': damage.frame_number,
                    'timestamp': damage.timestamp
                }
                for damage in detection.damages
            ],
            'statistics': {
                'total_frames_processed': detection.statistics.total_frames_processed,
                'total_damages_detected': detection.statistics.total_damages_detected,
                'damages_by_type': detection.statistics.damages_by_type,
                'damages_by_severity': detection.statistics.damages_by_severity,
                'average_confidence': detection.statistics.average_confidence,
                'processing_time': detection.statistics.processing_time,
                'frames_per_second': detection.statistics.frames_per_second
            },
            'created_at': detection.created_at.isoformat(),
            'model_version': detection.model_version,
            'confidence_threshold': detection.confidence_threshold,
            'output_path': str(detection.output_path) if detection.output_path else None,
            'annotated_video_path': str(detection.annotated_video_path) if detection.annotated_video_path else None
        }
    
    def _dict_to_detection(self, data: Dict[str, Any]) -> DetectionResult:
        """Convierte un diccionario a DetectionResult."""
        # Crear video
        video_data = data['video']
        metadata = None
        if video_data.get('metadata'):
            metadata_data = video_data['metadata']
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
        
        video = Video(
            id=video_data['id'],
            name=video_data['name'],
            file_path=Path(video_data['file_path']),
            status=VideoStatus(video_data['status']),
            created_at=datetime.fromisoformat(video_data['created_at']),
            metadata=metadata
        )
        
        # Crear daños
        damages = []
        for damage_data in data['damages']:
            bbox = BoundingBox(
                x1=damage_data['bounding_box']['x1'],
                y1=damage_data['bounding_box']['y1'],
                x2=damage_data['bounding_box']['x2'],
                y2=damage_data['bounding_box']['y2']
            )
            
            damage = Damage(
                id=damage_data['id'],
                damage_type=DamageType(damage_data['damage_type']),
                severity=DamageSeverity(damage_data['severity']),
                confidence=damage_data['confidence'],
                bounding_box=bbox,
                frame_number=damage_data['frame_number'],
                timestamp=damage_data['timestamp']
            )
            damages.append(damage)
        
        # Crear estadísticas
        stats_data = data['statistics']
        statistics = DetectionStatistics(
            total_frames_processed=stats_data['total_frames_processed'],
            total_damages_detected=stats_data['total_damages_detected'],
            damages_by_type=stats_data['damages_by_type'],
            damages_by_severity=stats_data['damages_by_severity'],
            average_confidence=stats_data['average_confidence'],
            processing_time=stats_data['processing_time'],
            frames_per_second=stats_data['frames_per_second']
        )
        
        # Crear resultado de detección
        detection_result = DetectionResult(
            id=data['id'],
            video=video,
            damages=damages,
            statistics=statistics,
            created_at=datetime.fromisoformat(data['created_at']),
            model_version=data['model_version'],
            confidence_threshold=data['confidence_threshold'],
            output_path=Path(data['output_path']) if data.get('output_path') else None,
            annotated_video_path=Path(data['annotated_video_path']) if data.get('annotated_video_path') else None
        )
        
        return detection_result