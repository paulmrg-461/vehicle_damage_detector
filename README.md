# Vehicle Damage Detection System

Sistema de detección de daños en vehículos utilizando YOLOv11 y arquitectura limpia (Clean Architecture).

## 🚀 Características

- **Detección automática de daños** en vehículos usando YOLOv11
- **API REST** completa para procesamiento de videos
- **Arquitectura limpia** siguiendo principios SOLID
- **Containerización** con Docker y Docker Compose
- **Procesamiento asíncrono** de videos
- **Almacenamiento persistente** de resultados
- **Logging estructurado** para monitoreo

## 🏗️ Arquitectura

El proyecto sigue los principios de Clean Architecture:

```
src/
├── domain/           # Entidades y reglas de negocio
│   ├── entities/     # Video, DetectionResult, Damage
│   └── repositories/ # Interfaces de repositorios
├── application/      # Casos de uso y servicios
│   └── services/     # VideoProcessingService, DamageDetectionService
├── infrastructure/   # Implementaciones técnicas
│   ├── ai/          # YOLOv11 integration
│   ├── repositories/ # Implementaciones de repositorios
│   └── config/      # Configuración y dependencias
└── presentation/     # Capa de presentación
    └── api/         # FastAPI endpoints y modelos
```

## 🛠️ Tecnologías

- **Python 3.11**
- **FastAPI** - Framework web moderno y rápido
- **YOLOv11** - Modelo de detección de objetos
- **OpenCV** - Procesamiento de video
- **Pydantic** - Validación de datos
- **Docker** - Containerización
- **Uvicorn** - Servidor ASGI

## 📋 Requisitos

- Docker y Docker Compose
- Videos de prueba (car1.mp4, car2.mp4)

## 🚀 Instalación y Uso

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd vehicle_damage_detector
```

### 2. Preparar videos de prueba

Coloca los videos de prueba en la carpeta `videos/`:
- `videos/car1.mp4`
- `videos/car2.mp4`

### 3. Construir y ejecutar con Docker

```bash
# Construir la imagen
docker-compose build

# Ejecutar la aplicación
docker-compose up -d
```

### 4. Verificar que la aplicación esté funcionando

```bash
# Verificar el estado del contenedor
docker ps

# Ver logs
docker logs vehicle_damage_detector_app
```

## 📡 API Endpoints

### Procesar Video

```http
POST /api/v1/videos/process
Content-Type: multipart/form-data

FormData:
- video: archivo de video (mp4)
- confidence_threshold: umbral de confianza (0.0-1.0)
```

**Ejemplo con PowerShell:**
```powershell
$form = @{
    video = Get-Item 'videos/car1.mp4'
    confidence_threshold = '0.5'
}
Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/videos/process' -Method POST -Form $form
```

### Listar Videos

```http
GET /api/v1/videos
```

**Parámetros de consulta:**
- `status`: filtrar por estado (processing, completed, failed)
- `page`: número de página (default: 1)
- `page_size`: tamaño de página (default: 10)

### Obtener Video Específico

```http
GET /api/v1/videos/{video_id}
```

### Documentación Interactiva

Accede a la documentación Swagger en:
- http://localhost:8000/docs
- http://localhost:8000/redoc

## 🔧 Configuración

### Variables de Entorno

El archivo `docker-compose.yml` incluye las siguientes configuraciones:

```yaml
environment:
  - PYTHONPATH=/app
  - LOG_LEVEL=INFO
  - DATA_PATH=/app/data
  - VIDEOS_PATH=/app/videos
```

### Volúmenes

- `./videos:/app/videos` - Videos de entrada
- `./data:/app/data` - Almacenamiento de datos persistente

## 📊 Estructura de Respuesta

### ProcessVideoResponse

```json
{
  "success": true,
  "message": "Video processed successfully",
  "timestamp": "2025-08-22T15:15:02.358833",
  "video_id": "595150b6-d009-4224-bea3-dbd9494fee03",
  "detection_result": {
    "id": "det_123",
    "video_id": "595150b6-d009-4224-bea3-dbd9494fee03",
    "damages": [
      {
        "id": "dmg_001",
        "type": "scratch",
        "confidence": 0.85,
        "bounding_box": {
          "x": 100,
          "y": 150,
          "width": 200,
          "height": 100
        },
        "frame_number": 45
      }
    ],
    "statistics": {
      "total_damages": 3,
      "frames_processed": 150,
      "processing_time_seconds": 12.5,
      "average_confidence": 0.78
    },
    "created_at": "2025-08-22T15:15:02.358833"
  }
}
```

### VideoListResponse

```json
{
  "success": true,
  "message": "Retrieved 5 videos",
  "timestamp": "2025-08-22T15:29:47.672221",
  "videos": [
    {
      "id": "595150b6-d009-4224-bea3-dbd9494fee03",
      "file_path": "/app/videos/car1.mp4",
      "status": "completed",
      "created_at": "2025-08-22T15:15:02.358833",
      "updated_at": null,
      "metadata": {
        "file_path": "/app/videos/car1.mp4",
        "duration_seconds": 30.5,
        "fps": 30,
        "width": 1920,
        "height": 1080,
        "format": "mp4",
        "file_size_mb": 4.06
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_count": 5,
    "total_pages": 1
  }
}
```

## 🐛 Solución de Problemas

### Problemas Comunes

1. **Error de conexión al contenedor**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

2. **Problemas de permisos con volúmenes**
   ```bash
   # En Linux/Mac
   sudo chown -R $USER:$USER ./data ./videos
   ```

3. **Ver logs detallados**
   ```bash
   docker logs vehicle_damage_detector_app --tail 50
   ```

### Verificación de Salud

La aplicación incluye verificaciones de salud automáticas:
- Repositorios de datos
- Servicios de procesamiento
- Modelo de detección YOLOv11

## 🧪 Testing

### Pruebas Manuales

1. **Procesar video de prueba:**
   ```bash
   # Usar car1.mp4 con umbral 0.5
   curl -X POST "http://localhost:8000/api/v1/videos/process" \
        -F "video=@videos/car1.mp4" \
        -F "confidence_threshold=0.5"
   ```

2. **Listar videos procesados:**
   ```bash
   curl "http://localhost:8000/api/v1/videos"
   ```

3. **Obtener video específico:**
   ```bash
   curl "http://localhost:8000/api/v1/videos/{video_id}"
   ```

## 📈 Monitoreo

### Logs

La aplicación genera logs estructurados con:
- Timestamp
- Nivel de log
- Módulo
- Mensaje
- Request ID para trazabilidad

### Métricas

- Tiempo de procesamiento por video
- Número de daños detectados
- Confianza promedio de detecciones
- Estado de salud de componentes

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👥 Autores

- **Desarrollador Principal** - Implementación inicial

## 🙏 Agradecimientos

- YOLOv11 por el modelo de detección
- FastAPI por el framework web
- OpenCV por las herramientas de procesamiento de video
- Docker por la containerización