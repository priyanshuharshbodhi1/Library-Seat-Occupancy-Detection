FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt requirements-api.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-api.txt

# Copy project files
COPY . .

# Download YOLOv7 weights if not present
RUN if [ ! -f yolov7.pt ]; then \
    wget https://github.com/WongKinYiu/yolov7/releases/download/v0.1/yolov7.pt; \
    fi

# Create necessary directories
RUN mkdir -p uploads outputs jobs api/logs

# Expose API port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the API server
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
