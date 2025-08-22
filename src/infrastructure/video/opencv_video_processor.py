import asyncio
from typing import List, Optional, Tuple, AsyncGenerator, Dict, Any
from pathlib import Path
import cv2
import numpy as np
from datetime import datetime
import logging
import json

from ...domain.entities.video import Video, VideoMetadata, VideoFormat
from ...domain.entities.detection_result import DetectionResult
from ...domain.entities.damage import Damage
from ...domain.services.video_processing_service import VideoProcessingService


class OpenCVVideoProcessor(VideoProcessingService):
    """Implementación del servicio de procesamiento de video usando OpenCV."""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
    
    async def extract_metadata(self, video_path: Path) -> VideoMetadata:
        """Extrae metadatos de un video."""
        if not video_path.exists():
            raise FileNotFoundError(f"El archivo de video no existe: {video_path}")
        
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise ValueError(f"No se pudo abrir el video: {video_path}")
            
            # Extraer propiedades del video
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            # Obtener información del archivo
            file_size = video_path.stat().st_size
            
            # Determinar formato
            format_name = video_path.suffix.lower()
            video_format = self._get_video_format(format_name)
            
            cap.release()
            
            metadata = VideoMetadata(
                duration=duration,
                fps=fps,
                width=width,
                height=height,
                frame_count=frame_count,
                file_size=file_size,
                format=video_format,
                codec=self._get_codec_info(video_path),
                bitrate=self._calculate_bitrate(file_size, duration)
            )
            
            self._logger.info(f"Metadatos extraídos para {video_path.name}: {width}x{height}, {fps}fps, {duration:.2f}s")
            
            return metadata
            
        except Exception as e:
            self._logger.error(f"Error al extraer metadatos de {video_path}: {e}")
            raise e
    
    async def validate_video(self, video_path: Path) -> bool:
        """Valida si un archivo de video es válido y procesable."""
        try:
            if not video_path.exists():
                return False
            
            if video_path.suffix.lower() not in self._supported_formats:
                return False
            
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return False
            
            # Intentar leer el primer frame
            ret, frame = cap.read()
            cap.release()
            
            return ret and frame is not None
            
        except Exception as e:
            self._logger.error(f"Error al validar video {video_path}: {e}")
            return False
    
    async def extract_frames(self, video: Video, frame_interval: int = 1) -> AsyncGenerator[Tuple[int, np.ndarray], None]:
        """Extrae frames de un video de forma asíncrona."""
        cap = cv2.VideoCapture(str(video.file_path))
        if not cap.isOpened():
            raise ValueError(f"No se pudo abrir el video: {video.file_path}")
        
        try:
            frame_number = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_number % frame_interval == 0:
                    yield (frame_number, frame)
                    
                    # Permitir que otros procesos se ejecuten
                    await asyncio.sleep(0)
                
                frame_number += 1
                
        finally:
            cap.release()
    
    async def get_frame_at_time(self, video: Video, timestamp: float) -> Optional[np.ndarray]:
        """Obtiene un frame específico en un tiempo dado."""
        try:
            cap = cv2.VideoCapture(str(video.file_path))
            if not cap.isOpened():
                return None
            
            # Convertir timestamp a número de frame
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(timestamp * fps)
            
            # Posicionar en el frame deseado
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            cap.release()
            
            return frame if ret else None
            
        except Exception as e:
            self._logger.error(f"Error al obtener frame en tiempo {timestamp}: {e}")
            return None
    
    async def get_frame_at_number(self, video: Video, frame_number: int) -> Optional[np.ndarray]:
        """Obtiene un frame específico por número."""
        try:
            cap = cv2.VideoCapture(str(video.file_path))
            if not cap.isOpened():
                return None
            
            # Posicionar en el frame deseado
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            cap.release()
            
            return frame if ret else None
            
        except Exception as e:
            self._logger.error(f"Error al obtener frame {frame_number}: {e}")
            return None
    
    async def create_annotated_video(self, video: Video, detection_result: DetectionResult, output_path: Path) -> Path:
        """Crea un video anotado con las detecciones."""
        try:
            # Asegurar que el directorio de salida existe
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            cap = cv2.VideoCapture(str(video.file_path))
            if not cap.isOpened():
                raise ValueError(f"No se pudo abrir el video: {video.file_path}")
            
            # Obtener propiedades del video original
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Configurar el escritor de video
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            
            # Agrupar daños por frame para eficiencia
            damages_by_frame = {}
            for damage in detection_result.damages:
                frame_num = damage.frame_number
                if frame_num not in damages_by_frame:
                    damages_by_frame[frame_num] = []
                damages_by_frame[frame_num].append(damage)
            
            frame_number = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Anotar frame si tiene daños detectados
                if frame_number in damages_by_frame:
                    frame = self._annotate_frame(frame, damages_by_frame[frame_number])
                
                out.write(frame)
                frame_number += 1
            
            cap.release()
            out.release()
            
            self._logger.info(f"Video anotado creado: {output_path}")
            
            return output_path
            
        except Exception as e:
            self._logger.error(f"Error al crear video anotado: {e}")
            raise e
    
    async def create_thumbnail(self, video: Video, output_path: Path, timestamp: float = 0.0) -> Path:
        """Crea una miniatura del video."""
        try:
            frame = await self.get_frame_at_time(video, timestamp)
            if frame is None:
                raise ValueError("No se pudo obtener el frame para la miniatura")
            
            # Redimensionar frame para miniatura
            height, width = frame.shape[:2]
            thumbnail_width = 320
            thumbnail_height = int(height * (thumbnail_width / width))
            
            thumbnail = cv2.resize(frame, (thumbnail_width, thumbnail_height))
            
            # Asegurar que el directorio existe
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Guardar miniatura
            cv2.imwrite(str(output_path), thumbnail)
            
            self._logger.info(f"Miniatura creada: {output_path}")
            
            return output_path
            
        except Exception as e:
            self._logger.error(f"Error al crear miniatura: {e}")
            raise e
    
    async def get_video_info(self, video_path: Path) -> dict:
        """Obtiene información detallada del video."""
        try:
            metadata = await self.extract_metadata(video_path)
            
            return {
                "file_name": video_path.name,
                "file_path": str(video_path),
                "file_size": metadata.file_size,
                "file_size_mb": round(metadata.file_size / (1024 * 1024), 2),
                "duration": metadata.duration,
                "duration_formatted": self._format_duration(metadata.duration),
                "fps": metadata.fps,
                "resolution": f"{metadata.width}x{metadata.height}",
                "width": metadata.width,
                "height": metadata.height,
                "frame_count": metadata.frame_count,
                "format": metadata.format.value,
                "codec": metadata.codec,
                "bitrate": metadata.bitrate,
                "aspect_ratio": round(metadata.width / metadata.height, 2)
            }
            
        except Exception as e:
            self._logger.error(f"Error al obtener información del video: {e}")
            raise e
    
    async def compress_video(self, input_path: Path, output_path: Path, quality: str = 'medium') -> Path:
        """Comprime un video."""
        # Esta funcionalidad requeriría FFmpeg para una compresión avanzada
        # Por ahora, implementamos una versión básica con OpenCV
        raise NotImplementedError("Compresión de video requiere FFmpeg")
    
    async def convert_format(self, input_path: Path, output_path: Path, target_format: str) -> Path:
        """Convierte un video a otro formato."""
        # Esta funcionalidad requeriría FFmpeg para conversiones avanzadas
        raise NotImplementedError("Conversión de formato requiere FFmpeg")
    
    async def get_supported_formats(self) -> List[str]:
        """Obtiene los formatos de video soportados."""
        return self._supported_formats.copy()
    
    def _get_video_format(self, extension: str) -> VideoFormat:
        """Determina el formato de video basado en la extensión."""
        format_mapping = {
            '.mp4': VideoFormat.MP4,
            '.avi': VideoFormat.AVI,
            '.mov': VideoFormat.MOV,
            '.mkv': VideoFormat.MKV,
            '.wmv': VideoFormat.WMV,
            '.flv': VideoFormat.FLV,
            '.webm': VideoFormat.WEBM
        }
        return format_mapping.get(extension, VideoFormat.UNKNOWN)
    
    def _get_codec_info(self, video_path: Path) -> str:
        """Obtiene información del codec (simplificado)."""
        # OpenCV no proporciona información detallada del codec
        # Retornamos información básica basada en la extensión
        extension = video_path.suffix.lower()
        codec_mapping = {
            '.mp4': 'H.264',
            '.avi': 'XVID',
            '.mov': 'H.264',
            '.mkv': 'H.264',
            '.wmv': 'WMV',
            '.flv': 'FLV',
            '.webm': 'VP8/VP9'
        }
        return codec_mapping.get(extension, 'Unknown')
    
    def _calculate_bitrate(self, file_size: int, duration: float) -> int:
        """Calcula el bitrate aproximado."""
        if duration <= 0:
            return 0
        return int((file_size * 8) / duration)  # bits por segundo
    
    def _format_duration(self, duration: float) -> str:
        """Formatea la duración en formato HH:MM:SS."""
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def _annotate_frame(self, frame: np.ndarray, damages: List[Damage]) -> np.ndarray:
        """Anota un frame con las detecciones de daños."""
        annotated_frame = frame.copy()
        
        # Colores para diferentes tipos de daño
        color_mapping = {
            'SCRATCH': (0, 255, 255),    # Amarillo
            'DENT': (255, 0, 0),         # Azul
            'CRACK': (0, 0, 255),        # Rojo
            'RUST': (0, 165, 255),       # Naranja
            'BROKEN_PART': (128, 0, 128), # Púrpura
            'UNKNOWN': (128, 128, 128)    # Gris
        }
        
        for damage in damages:
            bbox = damage.bounding_box
            color = color_mapping.get(damage.damage_type.value, (255, 255, 255))
            
            # Dibujar rectángulo
            cv2.rectangle(
                annotated_frame,
                (int(bbox.x1), int(bbox.y1)),
                (int(bbox.x2), int(bbox.y2)),
                color,
                2
            )
            
            # Agregar etiqueta
            label = f"{damage.damage_type.value} ({damage.confidence:.2f})"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            
            # Fondo para el texto
            cv2.rectangle(
                annotated_frame,
                (int(bbox.x1), int(bbox.y1) - label_size[1] - 10),
                (int(bbox.x1) + label_size[0], int(bbox.y1)),
                color,
                -1
            )
            
            # Texto
            cv2.putText(
                annotated_frame,
                label,
                (int(bbox.x1), int(bbox.y1) - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
        
        return annotated_frame