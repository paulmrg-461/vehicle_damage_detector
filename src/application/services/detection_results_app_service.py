from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pathlib import Path
import asyncio

from src.domain.entities.detection_result import DetectionResult
from src.domain.entities.damage import DamageType, DamageSeverity
from src.domain.use_cases.get_detection_results_use_case import GetDetectionResultsUseCase
from src.infrastructure.config.logging_config import LoggerMixin
from src.infrastructure.config.settings import get_settings


class DetectionResultsAppService(LoggerMixin):
    """Servicio de aplicación para la gestión de resultados de detección."""
    
    def __init__(self, get_detection_results_use_case: GetDetectionResultsUseCase):
        self.get_detection_results_use_case = get_detection_results_use_case
        self.settings = get_settings()
        self.log_info("DetectionResultsAppService inicializado")
    
    async def get_result_by_id(self, result_id: str) -> Optional[DetectionResult]:
        """Obtiene un resultado de detección por su ID."""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self.get_detection_results_use_case.get_by_id,
                result_id
            )
        except Exception as e:
            self.log_error(f"Error obteniendo resultado {result_id}: {str(e)}")
            return None
    
    async def get_results_by_video_id(self, video_id: str) -> Optional[DetectionResult]:
        """Obtiene los resultados de detección para un video específico."""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self.get_detection_results_use_case.get_by_video_id,
                video_id
            )
        except Exception as e:
            self.log_error(f"Error obteniendo resultados para video {video_id}: {str(e)}")
            return None
    
    async def get_results_by_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[DetectionResult]:
        """Obtiene resultados de detección en un rango de fechas."""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self.get_detection_results_use_case.get_by_date_range,
                start_date,
                end_date
            )
        except Exception as e:
            self.log_error(f"Error obteniendo resultados por fecha {start_date} - {end_date}: {str(e)}")
            return []
    
    async def get_results_by_damage_type(
        self,
        damage_type: DamageType
    ) -> List[DetectionResult]:
        """Obtiene resultados que contienen un tipo específico de daño."""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self.get_detection_results_use_case.get_by_damage_type,
                damage_type
            )
        except Exception as e:
            self.log_error(f"Error obteniendo resultados por tipo de daño {damage_type}: {str(e)}")
            return []
    
    async def get_results_by_severity(
        self,
        min_severity: DamageSeverity
    ) -> List[DetectionResult]:
        """Obtiene resultados con daños de severidad mínima especificada."""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self.get_detection_results_use_case.get_by_severity,
                min_severity
            )
        except Exception as e:
            self.log_error(f"Error obteniendo resultados por severidad {min_severity}: {str(e)}")
            return []
    
    async def get_all_results(self) -> List[DetectionResult]:
        """Obtiene todos los resultados de detección."""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self.get_detection_results_use_case.get_all
            )
        except Exception as e:
            self.log_error(f"Error obteniendo todos los resultados: {str(e)}")
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales de detección."""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self.get_detection_results_use_case.get_statistics
            )
        except Exception as e:
            self.log_error(f"Error obteniendo estadísticas: {str(e)}")
            return {"error": str(e)}
    
    async def get_summary_by_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un resumen de detecciones para un video específico."""
        try:
            result = await self.get_results_by_video_id(video_id)
            if not result:
                return None
            
            return {
                "video_id": video_id,
                "total_damages": len(result.damages),
                "damage_types": self._count_damage_types(result.damages),
                "severity_distribution": self._count_severity_distribution(result.damages),
                "processing_time": result.statistics.processing_time_seconds,
                "total_frames": result.statistics.total_frames_processed,
                "confidence_threshold": result.confidence_threshold,
                "model_version": result.model_version,
                "created_at": result.created_at.isoformat()
            }
        except Exception as e:
            self.log_error(f"Error generando resumen para video {video_id}: {str(e)}")
            return None
    
    async def get_damage_trends(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """Obtiene tendencias de daños en los últimos N días."""
        try:
            end_date = date.today()
            start_date = date.fromordinal(end_date.toordinal() - days)
            
            results = await self.get_results_by_date_range(start_date, end_date)
            
            # Agrupar por fecha
            daily_stats = {}
            for result in results:
                result_date = result.created_at.date()
                if result_date not in daily_stats:
                    daily_stats[result_date] = {
                        "total_videos": 0,
                        "total_damages": 0,
                        "damage_types": {},
                        "avg_processing_time": 0
                    }
                
                daily_stats[result_date]["total_videos"] += 1
                daily_stats[result_date]["total_damages"] += len(result.damages)
                daily_stats[result_date]["avg_processing_time"] += result.statistics.processing_time_seconds
                
                # Contar tipos de daño
                for damage in result.damages:
                    damage_type = damage.damage_type.value
                    if damage_type not in daily_stats[result_date]["damage_types"]:
                        daily_stats[result_date]["damage_types"][damage_type] = 0
                    daily_stats[result_date]["damage_types"][damage_type] += 1
            
            # Calcular promedios
            for date_key in daily_stats:
                if daily_stats[date_key]["total_videos"] > 0:
                    daily_stats[date_key]["avg_processing_time"] /= daily_stats[date_key]["total_videos"]
            
            return {
                "period": f"{start_date} to {end_date}",
                "total_days": days,
                "daily_statistics": {
                    str(date_key): stats for date_key, stats in daily_stats.items()
                },
                "summary": {
                    "total_videos_processed": len(results),
                    "total_damages_detected": sum(len(r.damages) for r in results),
                    "avg_damages_per_video": sum(len(r.damages) for r in results) / len(results) if results else 0
                }
            }
        except Exception as e:
            self.log_error(f"Error obteniendo tendencias de daños: {str(e)}")
            return {"error": str(e)}
    
    async def export_results_to_dict(
        self,
        video_ids: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Exporta resultados a formato diccionario para serialización."""
        try:
            results = []
            
            if video_ids:
                # Obtener resultados por IDs de video específicos
                for video_id in video_ids:
                    result = await self.get_results_by_video_id(video_id)
                    if result:
                        results.append(result)
            elif start_date and end_date:
                # Obtener resultados por rango de fechas
                results = await self.get_results_by_date_range(start_date, end_date)
            else:
                # Obtener todos los resultados
                results = await self.get_all_results()
            
            # Convertir a diccionarios
            exported_data = []
            for result in results:
                result_dict = result.to_dict()
                exported_data.append(result_dict)
            
            self.log_info(f"Exportados {len(exported_data)} resultados")
            return exported_data
            
        except Exception as e:
            self.log_error(f"Error exportando resultados: {str(e)}")
            return []
    
    def _count_damage_types(self, damages) -> Dict[str, int]:
        """Cuenta la distribución de tipos de daño."""
        counts = {}
        for damage in damages:
            damage_type = damage.damage_type.value
            counts[damage_type] = counts.get(damage_type, 0) + 1
        return counts
    
    def _count_severity_distribution(self, damages) -> Dict[str, int]:
        """Cuenta la distribución de severidad de daños."""
        counts = {}
        for damage in damages:
            severity = damage.severity.value
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    async def get_recent_results(self, limit: int = 10) -> List[DetectionResult]:
        """Obtiene los resultados más recientes."""
        try:
            all_results = await self.get_all_results()
            # Ordenar por fecha de creación descendente
            sorted_results = sorted(
                all_results,
                key=lambda x: x.created_at,
                reverse=True
            )
            return sorted_results[:limit]
        except Exception as e:
            self.log_error(f"Error obteniendo resultados recientes: {str(e)}")
            return []
    
    async def search_results(
        self,
        query: str,
        search_in_video_path: bool = True,
        search_in_model_version: bool = True
    ) -> List[DetectionResult]:
        """Busca resultados basado en una consulta de texto."""
        try:
            all_results = await self.get_all_results()
            matching_results = []
            
            query_lower = query.lower()
            
            for result in all_results:
                match_found = False
                
                if search_in_video_path and result.video_metadata:
                    if query_lower in str(result.video_metadata.file_path).lower():
                        match_found = True
                
                if search_in_model_version and result.model_version:
                    if query_lower in result.model_version.lower():
                        match_found = True
                
                if match_found:
                    matching_results.append(result)
            
            self.log_info(f"Búsqueda '{query}' encontró {len(matching_results)} resultados")
            return matching_results
            
        except Exception as e:
            self.log_error(f"Error en búsqueda de resultados: {str(e)}")
            return []