# Library Seat Occupancy Detection API

## 🚀 Quick Start

### Installation

#### Option 1: Docker (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f api

# Stop the service
docker-compose down
```

The API will be available at `http://localhost:8000`

#### Option 2: Local Installation

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-api.txt

# Download model weights
python download_models.py

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Run the API server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📚 API Documentation

### Interactive Documentation

Once the server is running, access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Base URL

```
http://localhost:8000
```

---

## 🔌 API Endpoints

### 1. Health Check

**GET** `/health`

Check if the API is running and healthy.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model_loaded": true,
  "timestamp": "2025-10-08T12:00:00"
}
```

---

### 2. Create Detection Job

**POST** `/api/detect`

Upload a video file to start a detection job.

**Request:**
- **Content-Type**: `multipart/form-data`
- **Body Parameters**:
  - `video` (file, required): Video file to process
  - `conf_threshold` (float, optional): Detection confidence threshold (0.0-1.0)
  - `iou_threshold` (float, optional): IOU threshold for NMS (0.0-1.0)
  - `occupancy_time_threshold` (int, optional): Time threshold in seconds
  - `save_video` (bool, optional): Save processed video (default: true)
  - `include_frame_stats` (bool, optional): Include frame statistics (default: false)

**Example using cURL:**
```bash
curl -X POST "http://localhost:8000/api/detect" \
  -F "video=@library_video.mp4" \
  -F "conf_threshold=0.3" \
  -F "save_video=true"
```

**Example using Python:**
```python
import requests

url = "http://localhost:8000/api/detect"
files = {"video": open("library_video.mp4", "rb")}
params = {
    "conf_threshold": 0.3,
    "save_video": True,
    "include_frame_stats": False
}

response = requests.post(url, files=files, params=params)
job = response.json()
print(f"Job ID: {job['job_id']}")
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Job created and submitted for processing",
  "created_at": "2025-10-08T12:00:00"
}
```

---

### 3. Get Job Status

**GET** `/api/jobs/{job_id}`

Get the status and results of a detection job.

**Example:**
```bash
curl "http://localhost:8000/api/jobs/550e8400-e29b-41d4-a716-446655440000"
```

**Response (Processing):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "created_at": "2025-10-08T12:00:00",
  "started_at": "2025-10-08T12:00:05",
  "completed_at": null,
  "progress": 45.5,
  "message": "Processing frame 150/330",
  "results": null,
  "output_video_url": null
}
```

**Response (Completed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2025-10-08T12:00:00",
  "started_at": "2025-10-08T12:00:05",
  "completed_at": "2025-10-08T12:02:30",
  "progress": 100.0,
  "message": "Completed: processed 330 frames",
  "results": {
    "total_frames": 330,
    "total_detections": 1245,
    "person_detections": 892,
    "chair_detections": 353,
    "unique_tracked_objects": 12,
    "occupancy_events": [
      {
        "seat_id": 1,
        "bbox": {"x1": 100, "y1": 200, "x2": 300, "y2": 400},
        "occupied_duration": 15.5,
        "time_exceeded": true,
        "first_detected_frame": 10,
        "last_detected_frame": 320
      }
    ],
    "processing_time": 145.3,
    "fps": 2.27
  },
  "output_video_url": "/api/download/550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 4. Download Processed Video

**GET** `/api/download/{job_id}`

Download the processed video file.

**Example:**
```bash
curl -O -J "http://localhost:8000/api/download/550e8400-e29b-41d4-a716-446655440000"
```

**Python Example:**
```python
import requests

job_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"http://localhost:8000/api/download/{job_id}"

response = requests.get(url)
with open(f"result_{job_id}.mp4", "wb") as f:
    f.write(response.content)
```

---

### 5. List All Jobs

**GET** `/api/jobs`

List all detection jobs with optional filtering.

**Query Parameters:**
- `limit` (int, optional): Maximum number of jobs (default: 100)
- `status` (string, optional): Filter by status (pending, processing, completed, failed)

**Example:**
```bash
curl "http://localhost:8000/api/jobs?limit=10&status=completed"
```

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "created_at": "2025-10-08T12:00:00",
      "progress": 100.0,
      "message": "Completed: processed 330 frames"
    }
  ],
  "total": 1
}
```

---

### 6. Delete Job

**DELETE** `/api/jobs/{job_id}`

Delete a job and its associated files.

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/jobs/550e8400-e29b-41d4-a716-446655440000"
```

**Response:**
```json
{
  "message": "Job 550e8400-e29b-41d4-a716-446655440000 deleted successfully"
}
```

---

### 7. Cleanup Old Jobs

**POST** `/api/cleanup`

Clean up old completed/failed jobs.

**Query Parameters:**
- `max_age_hours` (int, optional): Maximum age in hours (default: 24)

**Example:**
```bash
curl -X POST "http://localhost:8000/api/cleanup?max_age_hours=48"
```

**Response:**
```json
{
  "message": "Cleaned up 5 old jobs",
  "jobs_cleaned": 5,
  "jobs_remaining": 10
}
```

---

## 📝 Complete Workflow Example

### Python Script

```python
import requests
import time
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
VIDEO_PATH = "library_video.mp4"

def main():
    # 1. Upload video and create job
    print("Uploading video...")
    with open(VIDEO_PATH, "rb") as video_file:
        response = requests.post(
            f"{API_BASE_URL}/api/detect",
            files={"video": video_file},
            params={
                "conf_threshold": 0.3,
                "save_video": True,
                "include_frame_stats": True
            }
        )

    if response.status_code != 200:
        print(f"Error: {response.json()}")
        return

    job = response.json()
    job_id = job["job_id"]
    print(f"Job created: {job_id}")

    # 2. Poll for job completion
    print("Waiting for processing to complete...")
    while True:
        response = requests.get(f"{API_BASE_URL}/api/jobs/{job_id}")
        status_data = response.json()

        status = status_data["status"]
        progress = status_data.get("progress", 0)

        print(f"Status: {status} - Progress: {progress:.1f}%")

        if status == "completed":
            print("Processing completed!")
            print(f"Results: {status_data['results']}")
            break
        elif status == "failed":
            print(f"Processing failed: {status_data.get('message')}")
            return

        time.sleep(2)  # Poll every 2 seconds

    # 3. Download processed video
    print("Downloading processed video...")
    response = requests.get(f"{API_BASE_URL}/api/download/{job_id}")

    output_path = f"processed_{job_id}.mp4"
    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"Downloaded to: {output_path}")

    # 4. Display results
    results = status_data["results"]
    print(f"\n=== Detection Results ===")
    print(f"Total Frames: {results['total_frames']}")
    print(f"Total Detections: {results['total_detections']}")
    print(f"Person Detections: {results['person_detections']}")
    print(f"Chair Detections: {results['chair_detections']}")
    print(f"Processing Time: {results['processing_time']:.2f}s")
    print(f"FPS: {results['fps']:.2f}")
    print(f"Occupancy Events: {len(results['occupancy_events'])}")

if __name__ == "__main__":
    main()
```

---

## 🔧 Configuration

### Environment Variables

All configuration is done via environment variables in `.env` file:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Model Configuration
MODEL_WEIGHTS_PATH=yolov7.pt
MODEL_CONF_THRESHOLD=0.25
MODEL_IOU_THRESHOLD=0.45

# Detection Classes (0=person, 56=chair)
DETECTION_CLASSES=0,56

# Occupancy Configuration
OCCUPANCY_TIME_THRESHOLD=10  # seconds

# Storage
MAX_UPLOAD_SIZE=524288000  # 500MB
ALLOWED_VIDEO_EXTENSIONS=mp4,avi,mov,mkv,webm

# Job Configuration
MAX_CONCURRENT_JOBS=3
JOB_CLEANUP_AFTER_HOURS=24
```

See `.env.example` for all available options.

---

## 🛠️ Troubleshooting

### Common Issues

**1. Port already in use**
```bash
# Change port in .env or docker-compose.yml
API_PORT=8001
```

**2. Out of memory**
```bash
# Reduce concurrent jobs in .env
MAX_CONCURRENT_JOBS=1
```

**3. Model weights not found**
```bash
# Download weights manually
python download_models.py
```

**4. Slow processing**
- Use GPU if available (set `MODEL_DEVICE=0`)
- Reduce video resolution
- Increase `MODEL_CONF_THRESHOLD` to filter detections

---

## 📊 Response Status Codes

- `200` - Success
- `400` - Bad request (invalid parameters)
- `404` - Resource not found (job or file)
- `413` - File too large
- `422` - Validation error
- `500` - Internal server error

---

## 🔒 Security Notes

- Enable API key authentication by setting `API_KEY_ENABLED=True` in `.env`
- Restrict CORS origins in production: `CORS_ORIGINS=https://yourdomain.com`
- Set file size limits: `MAX_UPLOAD_SIZE=524288000`
- Regular cleanup of old jobs: `JOB_CLEANUP_AFTER_HOURS=24`

---

## 📈 Performance Tips

1. **GPU Acceleration**: Set `MODEL_DEVICE=0` to use GPU
2. **Concurrent Jobs**: Adjust `MAX_CONCURRENT_JOBS` based on system resources
3. **Video Preprocessing**: Resize large videos before upload
4. **Caching**: Processed results are cached in the `jobs/` directory

---

## 🤝 Support

For issues and questions:
- GitHub Issues: https://github.com/priyanshuharshbodhi1/Library-Seat-Occupancy-Detection/issues
- Email: asumansaree@gmail.com

---

## 📄 License

MIT License - See LICENSE file for details
