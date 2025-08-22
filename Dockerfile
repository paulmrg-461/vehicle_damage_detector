FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    libgtk-3-0 \
    ffmpeg \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/ ./src/
COPY config/ ./config/

# Crear directorios necesarios
RUN mkdir -p logs output videos

# Exponer puerto para la API
EXPOSE 8000

# Comando por defecto
CMD ["python", "-m", "uvicorn", "src.presentation.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]