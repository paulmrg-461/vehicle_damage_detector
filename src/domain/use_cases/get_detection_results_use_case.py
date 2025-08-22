from typing import List, Optional, Dict
from datetime import datetime

from ..entities.detection_result import DetectionResult
from ..entities.damage import DamageType, DamageSeverity
from ..repositories.detection_repository import DetectionRepository
from ..repositories.video_repository import VideoRepository


class GetDetectionResultsUseCase:
    """Caso de uso para obtener y consultar resultados de detección."""
    
    def __init__(
        self,
        detection_repository: DetectionRepository,
        video_repository: VideoRepository
    ):
        self._detection_repository = detection_repository
        self._video_repository = video_repository
    
    async def get_by_id(self, result_id: str) -> Optional[DetectionResult]:
        """Obtiene un resultado de detección por ID."""
        return await self._detection_repository.find_by_id(result_id)
    
    async def get_by_video_id(self, video_id: str) -> List[DetectionResult]:
        """Obtiene todos los resultados de detección para un video."""
        return await self._detection_repository.find_by_video_id(video_id)
    
    async def get_all_results(self) -> List[DetectionResult]:
        """Obtiene todos los resultados de detección."""
        return await self._detection_repository.find_all()
    
    async def get_results_with_damages(self) -> List[DetectionResult]:
        """Obtiene solo los resultados que contienen daños detectados."""
        return await self._detection_repository.find_with_damages()
    
    async def get_results_by_damage_type(self, damage_type: DamageType) -> List[DetectionResult]:
        """Obtiene resultados que contienen un tipo específico de daño."""
        return await self._detection_repository.find_by_damage_type(damage_type.value)
    
    async def get_results_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[DetectionResult]:
        """Obtiene resultados en un rango de fechas."""
        return await self._detection_repository.find_by_date_range(start_date, end_date)
    
    async def get_severe_damage_results(self) -> List[DetectionResult]:
        """Obtiene resultados que contienen daños severos o críticos."""
        all_results = await self._detection_repository.find_with_damages()
        return [
            result for result in all_results 
            if any(damage.is_severe() for damage in result.damages)
        ]
    
    async def get_statistics(self) -> Dict[str, any]:
        """Obtiene estadísticas generales de todas las detecciones."""
        base_stats = await self._detection_repository.get_statistics()
        
        # Obtener estadísticas adicionales
        all_results = await self._detection_repository.find_all()
        results_with_damages = await self._detection_repository.find_with_damages()
        
        # Calcular estadísticas por tipo de daño
        damage_type_stats = {}
        severity_stats = {}
        
        for result in results_with_damages:
            for damage in result.damages:
                # Estadísticas por tipo
                damage_type = damage.damage_type.value
                if damage_type not in damage_type_stats:
                    damage_type_stats[damage_type] = 0
                damage_type_stats[damage_type] += 1
                
                # Estadísticas por severidad
                severity = damage.severity.value
                if severity not in severity_stats:
                    severity_stats[severity] = 0
                severity_stats[severity] += 1
        
        # Combinar estadísticas
        enhanced_stats = {
            **base_stats,
            "total_processed_videos": len(all_results),
            "videos_with_damages": len(results_with_damages),
            "videos_without_damages": len(all_results) - len(results_with_damages),
            "damage_detection_rate": len(results_with_damages) / len(all_results) if all_results else 0,
            "damage_types_distribution": damage_type_stats,
            "severity_distribution": severity_stats
        }
        
        return enhanced_stats
    
    async def get_summary_by_video(self, video_id: str) -> Optional[Dict[str, any]]:
        """Obtiene un resumen de detecciones para un video específico."""
        video = await self._video_repository.find_by_id(video_id)
        if not video:
            return None
        
        results = await self._detection_repository.find_by_video_id(video_id)
        if not results:
            return {
                "video_id": video_id,
                "video_name": video.name,
                "status": video.status.value,
                "has_results": False,
                "total_detections": 0
            }
        
        # Tomar el resultado más reciente
        latest_result = max(results, key=lambda r: r.created_at)
        
        return {
            "video_id": video_id,
            "video_name": video.name,
            "status": video.status.value,
            "has_results": True,
            "latest_detection": latest_result.generate_summary(),
            "total_detections": len(results),
            "detection_history": [
                {
                    "id": result.id,
                    "created_at": result.created_at.isoformat(),
                    "damage_count": result.damage_count,
                    "model_version": result.model_version
                }
                for result in sorted(results, key=lambda r: r.created_at, reverse=True)
            ]
        }
    
    async def search_results(
        self,
        damage_types: Optional[List[DamageType]] = None,
        min_confidence: Optional[float] = None,
        severity_levels: Optional[List[DamageSeverity]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[DetectionResult]:
        """Busca resultados con filtros múltiples."""
        results = await self._detection_repository.find_all()
        
        # Aplicar filtros
        if start_date or end_date:
            if start_date and end_date:
                results = [r for r in results if start_date <= r.created_at <= end_date]
            elif start_date:
                results = [r for r in results if r.created_at >= start_date]
            elif end_date:
                results = [r for r in results if r.created_at <= end_date]
        
        if damage_types:
            damage_type_values = [dt.value for dt in damage_types]
            results = [
                r for r in results 
                if any(d.damage_type.value in damage_type_values for d in r.damages)
            ]
        
        if min_confidence is not None:
            results = [
                r for r in results 
                if any(d.confidence >= min_confidence for d in r.damages)
            ]
        
        if severity_levels:
            severity_values = [sl.value for sl in severity_levels]
            results = [
                r for r in results 
                if any(d.severity.value in severity_values for d in r.damages)
            ]
        
        return results