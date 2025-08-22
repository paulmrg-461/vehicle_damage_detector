from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import asyncio
import aiofiles
import shutil
from datetime import datetime
import mimetypes

from src.infrastructure.config.logging_config import LoggerMixin
from src.infrastructure.config.settings import get_settings


class FileManagementAppService(LoggerMixin):
    """Servicio de aplicación para la gestión de archivos."""
    
    def __init__(self):
        self.settings = get_settings()
        self.log_info("FileManagementAppService inicializado")
    
    async def validate_video_file(self, file_path: Path) -> Dict[str, Any]:
        """Valida un archivo de video y retorna información sobre su validez."""
        validation_result = {
            "is_valid": False,
            "file_exists": False,
            "is_supported_format": False,
            "size_valid": False,
            "file_size_mb": 0,
            "mime_type": None,
            "errors": []
        }
        
        try:
            # Verificar existencia del archivo
            if not file_path.exists():
                validation_result["errors"].append(f"El archivo no existe: {file_path}")
                return validation_result
            
            validation_result["file_exists"] = True
            
            # Verificar si es un archivo (no directorio)
            if not file_path.is_file():
                validation_result["errors"].append(f"La ruta no es un archivo: {file_path}")
                return validation_result
            
            # Verificar formato soportado
            if not self.settings.is_supported_format(file_path):
                validation_result["errors"].append(
                    f"Formato no soportado: {file_path.suffix}. "
                    f"Formatos soportados: {', '.join(self.settings.supported_formats)}"
                )
            else:
                validation_result["is_supported_format"] = True
            
            # Verificar tamaño del archivo
            file_size = file_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            validation_result["file_size_mb"] = round(file_size_mb, 2)
            
            if file_size > self.settings.max_video_size_bytes:
                validation_result["errors"].append(
                    f"Archivo demasiado grande: {file_size_mb:.2f}MB. "
                    f"Máximo permitido: {self.settings.max_video_size_mb}MB"
                )
            else:
                validation_result["size_valid"] = True
            
            # Obtener tipo MIME
            mime_type, _ = mimetypes.guess_type(str(file_path))
            validation_result["mime_type"] = mime_type
            
            # Determinar si es válido en general
            validation_result["is_valid"] = (
                validation_result["file_exists"] and
                validation_result["is_supported_format"] and
                validation_result["size_valid"]
            )
            
            if validation_result["is_valid"]:
                self.log_info(f"Archivo de video válido: {file_path} ({file_size_mb:.2f}MB)")
            else:
                self.log_warning(f"Archivo de video inválido: {file_path} - Errores: {validation_result['errors']}")
            
            return validation_result
            
        except Exception as e:
            error_msg = f"Error validando archivo {file_path}: {str(e)}"
            self.log_error(error_msg)
            validation_result["errors"].append(error_msg)
            return validation_result
    
    async def discover_videos_in_directory(self, directory_path: Path) -> List[Path]:
        """Descubre todos los archivos de video en un directorio."""
        try:
            if not directory_path.exists() or not directory_path.is_dir():
                self.log_error(f"Directorio no válido: {directory_path}")
                return []
            
            video_files = []
            
            # Buscar archivos de video recursivamente
            for file_path in directory_path.rglob("*"):
                if file_path.is_file() and self.settings.is_supported_format(file_path):
                    video_files.append(file_path)
            
            self.log_info(f"Encontrados {len(video_files)} archivos de video en {directory_path}")
            return sorted(video_files)
            
        except Exception as e:
            self.log_error(f"Error descubriendo videos en {directory_path}: {str(e)}")
            return []
    
    async def copy_video_to_workspace(self, source_path: Path, filename: str = None) -> Path:
        """Copia un video al directorio de trabajo de la aplicación."""
        try:
            if not source_path.exists():
                raise FileNotFoundError(f"Archivo fuente no existe: {source_path}")
            
            # Generar nombre de archivo si no se proporciona
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{source_path.name}"
            
            destination_path = self.settings.videos_dir / filename
            
            # Asegurar que el directorio de destino existe
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copiar archivo
            await asyncio.get_event_loop().run_in_executor(
                None,
                shutil.copy2,
                str(source_path),
                str(destination_path)
            )
            
            self.log_info(f"Video copiado: {source_path} -> {destination_path}")
            return destination_path
            
        except Exception as e:
            self.log_error(f"Error copiando video {source_path}: {str(e)}")
            raise
    
    async def move_video_to_workspace(self, source_path: Path, filename: str = None) -> Path:
        """Mueve un video al directorio de trabajo de la aplicación."""
        try:
            if not source_path.exists():
                raise FileNotFoundError(f"Archivo fuente no existe: {source_path}")
            
            # Generar nombre de archivo si no se proporciona
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{source_path.name}"
            
            destination_path = self.settings.videos_dir / filename
            
            # Asegurar que el directorio de destino existe
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Mover archivo
            await asyncio.get_event_loop().run_in_executor(
                None,
                shutil.move,
                str(source_path),
                str(destination_path)
            )
            
            self.log_info(f"Video movido: {source_path} -> {destination_path}")
            return destination_path
            
        except Exception as e:
            self.log_error(f"Error moviendo video {source_path}: {str(e)}")
            raise
    
    async def cleanup_output_files(self, older_than_days: int = 7) -> Dict[str, Any]:
        """Limpia archivos de salida antiguos."""
        try:
            cutoff_time = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)
            
            deleted_files = []
            total_size_freed = 0
            
            # Limpiar directorio de salida
            if self.settings.output_dir.exists():
                for file_path in self.settings.output_dir.rglob("*"):
                    if file_path.is_file():
                        file_mtime = file_path.stat().st_mtime
                        if file_mtime < cutoff_time:
                            file_size = file_path.stat().st_size
                            await asyncio.get_event_loop().run_in_executor(
                                None,
                                file_path.unlink
                            )
                            deleted_files.append(str(file_path))
                            total_size_freed += file_size
            
            # Limpiar logs antiguos
            if self.settings.logs_dir.exists():
                for file_path in self.settings.logs_dir.rglob("*.log*"):
                    if file_path.is_file():
                        file_mtime = file_path.stat().st_mtime
                        if file_mtime < cutoff_time:
                            file_size = file_path.stat().st_size
                            await asyncio.get_event_loop().run_in_executor(
                                None,
                                file_path.unlink
                            )
                            deleted_files.append(str(file_path))
                            total_size_freed += file_size
            
            result = {
                "deleted_files_count": len(deleted_files),
                "deleted_files": deleted_files,
                "total_size_freed_mb": round(total_size_freed / (1024 * 1024), 2),
                "older_than_days": older_than_days
            }
            
            self.log_info(
                f"Limpieza completada: {len(deleted_files)} archivos eliminados, "
                f"{result['total_size_freed_mb']}MB liberados"
            )
            
            return result
            
        except Exception as e:
            self.log_error(f"Error en limpieza de archivos: {str(e)}")
            return {"error": str(e)}
    
    async def get_disk_usage(self) -> Dict[str, Any]:
        """Obtiene información sobre el uso de disco de los directorios de la aplicación."""
        try:
            def get_directory_size(directory: Path) -> int:
                """Calcula el tamaño total de un directorio."""
                total_size = 0
                if directory.exists():
                    for file_path in directory.rglob("*"):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
                return total_size
            
            # Calcular tamaños de directorios
            videos_size = await asyncio.get_event_loop().run_in_executor(
                None, get_directory_size, self.settings.videos_dir
            )
            output_size = await asyncio.get_event_loop().run_in_executor(
                None, get_directory_size, self.settings.output_dir
            )
            logs_size = await asyncio.get_event_loop().run_in_executor(
                None, get_directory_size, self.settings.logs_dir
            )
            
            # Obtener espacio libre en disco
            disk_usage = shutil.disk_usage(self.settings.base_dir)
            
            return {
                "directories": {
                    "videos": {
                        "path": str(self.settings.videos_dir),
                        "size_mb": round(videos_size / (1024 * 1024), 2)
                    },
                    "output": {
                        "path": str(self.settings.output_dir),
                        "size_mb": round(output_size / (1024 * 1024), 2)
                    },
                    "logs": {
                        "path": str(self.settings.logs_dir),
                        "size_mb": round(logs_size / (1024 * 1024), 2)
                    }
                },
                "disk_usage": {
                    "total_gb": round(disk_usage.total / (1024 * 1024 * 1024), 2),
                    "used_gb": round(disk_usage.used / (1024 * 1024 * 1024), 2),
                    "free_gb": round(disk_usage.free / (1024 * 1024 * 1024), 2),
                    "usage_percentage": round((disk_usage.used / disk_usage.total) * 100, 2)
                },
                "total_app_size_mb": round((videos_size + output_size + logs_size) / (1024 * 1024), 2)
            }
            
        except Exception as e:
            self.log_error(f"Error obteniendo uso de disco: {str(e)}")
            return {"error": str(e)}
    
    async def create_backup_of_results(self, backup_path: Path = None) -> Path:
        """Crea una copia de seguridad de los resultados y configuración."""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.settings.base_dir / f"backup_{timestamp}"
            
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copiar archivos de datos
            if self.settings.storage_path.exists():
                backup_data_path = backup_path / "data"
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    shutil.copytree,
                    str(self.settings.storage_path),
                    str(backup_data_path),
                    dirs_exist_ok=True
                )
            
            # Copiar configuración
            if self.settings.config_dir.exists():
                backup_config_path = backup_path / "config"
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    shutil.copytree,
                    str(self.settings.config_dir),
                    str(backup_config_path),
                    dirs_exist_ok=True
                )
            
            # Crear archivo de información del backup
            backup_info = {
                "created_at": datetime.now().isoformat(),
                "app_version": self.settings.app_version,
                "backup_path": str(backup_path)
            }
            
            info_file = backup_path / "backup_info.txt"
            async with aiofiles.open(info_file, 'w') as f:
                for key, value in backup_info.items():
                    await f.write(f"{key}: {value}\n")
            
            self.log_info(f"Backup creado exitosamente en: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.log_error(f"Error creando backup: {str(e)}")
            raise
    
    async def list_files_in_directory(
        self,
        directory_path: Path,
        file_extensions: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Lista archivos en un directorio con información detallada."""
        try:
            if not directory_path.exists() or not directory_path.is_dir():
                return []
            
            files_info = []
            
            for file_path in directory_path.iterdir():
                if file_path.is_file():
                    # Filtrar por extensiones si se especifican
                    if file_extensions and file_path.suffix.lower() not in file_extensions:
                        continue
                    
                    stat_info = file_path.stat()
                    file_info = {
                        "name": file_path.name,
                        "path": str(file_path),
                        "size_mb": round(stat_info.st_size / (1024 * 1024), 2),
                        "modified_at": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                        "extension": file_path.suffix.lower(),
                        "is_supported_video": self.settings.is_supported_format(file_path)
                    }
                    files_info.append(file_info)
            
            # Ordenar por fecha de modificación (más reciente primero)
            files_info.sort(key=lambda x: x["modified_at"], reverse=True)
            
            return files_info
            
        except Exception as e:
            self.log_error(f"Error listando archivos en {directory_path}: {str(e)}")
            return []