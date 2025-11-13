# Real-Time Webcam Seat Occupancy Detection Guide

## Overview

This system provides **real-time seat occupancy detection and monitoring** using your webcam. It detects people and chairs, tracks seat occupancy, monitors duration, and displays everything in a beautiful web dashboard.

## Features

✅ **Real-time webcam detection** with YOLOv7
✅ **Live video streaming** with bounding boxes
✅ **Seat occupancy tracking** with duration monitoring
✅ **Time exceeded alerts** for seats occupied too long
✅ **Beautiful web dashboard** with live statistics
✅ **REST API** for integration with other systems
✅ **Multiple camera support**

---

## Quick Start

### Method 1: Using Python Directly

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-api.txt
   ```

2. **Download Model Weights** (if not already downloaded)
   ```bash
   python download_models.py
   ```

3. **Start the API Server**
   ```bash
   python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Open Your Browser**
   Navigate to: **http://localhost:8000**

5. **Start Monitoring**
   - Click "Start Camera" button
   - Point your webcam at the seating area
   - Watch real-time occupancy updates!

### Method 2: Using Docker (Recommended)

```bash
# Build and start
docker-compose up --build

# Access the dashboard
# Open http://localhost:8000 in your browser
```

---

## Web Dashboard Guide

### Main Interface

The dashboard is divided into two main sections:

#### 1. Live Camera Feed (Left Panel)
- **Camera Selection**: Choose which camera to use (0, 1, 2)
- **Start/Stop Controls**: Control the webcam stream
- **Live Video**: See real-time detection with bounding boxes
- **Status Indicator**: Shows if camera is running or stopped

#### 2. Statistics Panel (Right Panel)
- **Total Seats**: Number of detected seats
- **Available Seats**: Seats currently available
- **Occupied Seats**: Seats currently in use
- **People Detected**: Real-time person count
- **Individual Seat Status**: Detailed list of each seat with:
  - Seat ID
  - Occupancy status (Occupied/Available)
  - Duration (how long the seat has been occupied)
  - ⚠️ TIME EXCEEDED warning if threshold reached

### Visual Indicators

- **Green boxes**: Available seats
- **Red boxes**: Occupied seats
- **Pulsing red**: Seats with time exceeded
- **Status dots**:
  - 🟢 Green = Available
  - 🔴 Red = Occupied

---

## API Endpoints

### Webcam Control

#### Start Webcam
```http
POST /api/webcam/start?camera_index=0
```

**Response:**
```json
{
  "message": "Webcam started successfully on camera 0",
  "status": "running",
  "camera_index": 0
}
```

#### Stop Webcam
```http
POST /api/webcam/stop
```

**Response:**
```json
{
  "message": "Webcam stopped successfully",
  "status": "stopped"
}
```

#### Get Status
```http
GET /api/webcam/status
```

**Response:**
```json
{
  "status": "running",
  "is_running": true,
  "occupancy_stats": {
    "total_seats": 12,
    "occupied_seats": 5,
    "available_seats": 7,
    "person_count": 5,
    "chair_count": 12
  }
}
```

### Real-Time Data

#### Video Stream
```http
GET /api/webcam/stream
```

Returns MJPEG stream with bounding boxes and annotations.

**Usage in HTML:**
```html
<img src="http://localhost:8000/api/webcam/stream" alt="Live Feed">
```

#### Occupancy Data
```http
GET /api/webcam/occupancy
```

**Response:**
```json
{
  "status": "running",
  "message": "Occupancy data retrieved successfully",
  "data": {
    "total_seats": 12,
    "occupied_seats": 5,
    "available_seats": 7,
    "person_count": 5,
    "chair_count": 12,
    "seats": [
      {
        "id": 1,
        "occupied": true,
        "duration": 45.2,
        "time_exceeded": true
      },
      {
        "id": 2,
        "occupied": false,
        "duration": 0,
        "time_exceeded": false
      }
    ]
  },
  "timestamp": 1699999999.123
}
```

---

## Configuration

Edit `.env` file to customize settings:

```bash
# Model Configuration
MODEL_CONF_THRESHOLD=0.4          # Detection confidence (0.0-1.0)
MODEL_IOU_THRESHOLD=0.45          # Overlap threshold
MODEL_DEVICE=                     # '' for auto, '0' for GPU, 'cpu' for CPU

# Occupancy Settings
OCCUPANCY_TIME_THRESHOLD=10       # Seconds before "TIME EXCEEDED" alert
OCCUPANCY_PROXIMITY_THRESHOLD=100 # Pixels for seat matching

# Detection Classes
DETECTION_CLASSES=0,56            # 0=person, 56=chair
```

---

## Use Cases

### 1. Library Seat Monitoring
Monitor available seats in real-time and display on screens for students.

### 2. Office Hot-Desking
Track desk usage and availability for flexible workspaces.

### 3. Restaurant Table Management
Monitor table occupancy and turnover times.

### 4. Waiting Room Management
Track wait times and seat availability in medical facilities.

### 5. Study Hall Monitoring
Monitor occupancy patterns and optimize space usage.

---

## Integration Examples

### JavaScript/React
```javascript
// Start webcam
const startWebcam = async () => {
  const response = await fetch('http://localhost:8000/api/webcam/start?camera_index=0', {
    method: 'POST'
  });
  const data = await response.json();
  console.log(data);
};

// Get occupancy data
const getOccupancy = async () => {
  const response = await fetch('http://localhost:8000/api/webcam/occupancy');
  const data = await response.json();
  return data.data;
};

// Poll for updates every second
setInterval(async () => {
  const stats = await getOccupancy();
  console.log(`Available seats: ${stats.available_seats}`);
}, 1000);
```

### Python
```python
import requests
import time

API_BASE = "http://localhost:8000"

# Start webcam
response = requests.post(f"{API_BASE}/api/webcam/start?camera_index=0")
print(response.json())

# Monitor occupancy
while True:
    response = requests.get(f"{API_BASE}/api/webcam/occupancy")
    data = response.json()

    if data['status'] == 'running':
        stats = data['data']
        print(f"Available: {stats['available_seats']}/{stats['total_seats']}")

        # Check for exceeded seats
        for seat in stats.get('seats', []):
            if seat['time_exceeded']:
                print(f"⚠️ Seat {seat['id']} has exceeded time limit!")

    time.sleep(1)
```

### Display Board Integration
```python
# For use with digital displays in libraries
import requests
from datetime import datetime

def get_display_message():
    response = requests.get("http://localhost:8000/api/webcam/occupancy")
    data = response.json()

    if data['status'] == 'running':
        stats = data['data']
        available = stats['available_seats']
        total = stats['total_seats']

        if available > 0:
            return f"✅ {available} Seats Available | Total: {total}"
        else:
            return f"❌ No Seats Available | Total: {total}"
    else:
        return "Monitoring System Offline"
```

---

## Troubleshooting

### Camera Not Starting

**Issue:** "Failed to start webcam on camera 0"

**Solutions:**
1. Check if another application is using the camera
2. Try a different camera index (1, 2, etc.)
3. Grant camera permissions to the terminal/application
4. On Windows: Check Privacy Settings > Camera

### Low FPS / Slow Processing

**Solutions:**
1. Use GPU if available:
   ```bash
   MODEL_DEVICE=0  # in .env
   ```
2. Reduce image size:
   ```bash
   MODEL_IMG_SIZE=416  # default is 640
   ```
3. Increase confidence threshold:
   ```bash
   MODEL_CONF_THRESHOLD=0.5  # default is 0.4
   ```

### No Seats Detected

**Solutions:**
1. Ensure chairs are visible in the camera frame
2. Adjust camera angle to show seating area clearly
3. Lower confidence threshold:
   ```bash
   MODEL_CONF_THRESHOLD=0.3
   ```
4. Ensure good lighting conditions

### Browser Shows "Camera Running" But No Video

**Solutions:**
1. Hard refresh the page (Ctrl+F5 or Cmd+Shift+R)
2. Check browser console for errors (F12)
3. Verify stream URL: http://localhost:8000/api/webcam/stream
4. Try a different browser

---

## Performance Optimization

### For Better Accuracy
```bash
MODEL_CONF_THRESHOLD=0.5    # Higher = fewer false positives
OCCUPANCY_PROXIMITY_THRESHOLD=80  # Lower = more precise seat matching
```

### For Better Speed
```bash
MODEL_IMG_SIZE=416          # Smaller = faster
MODEL_CONF_THRESHOLD=0.6    # Higher = less processing
```

### For GPU Acceleration
```bash
MODEL_DEVICE=0              # Use first GPU
```

---

## Security Considerations

1. **Network Security**
   - Use HTTPS in production
   - Set `CORS_ORIGINS` to specific domains
   - Enable API key authentication

2. **Privacy**
   - Inform users about video monitoring
   - Store minimal personal data
   - Consider blurring faces if needed

3. **Access Control**
   - Use firewall to restrict access
   - Enable API key authentication:
     ```bash
     API_KEY_ENABLED=True
     API_KEY=your-secret-key-here
     ```

---

## Advanced Features

### Custom Time Thresholds Per Seat

Modify `api/services/webcam_service.py` to set different thresholds:

```python
# Example: Different thresholds for different seat types
seat_thresholds = {
    'study': 120,  # 2 hours for study seats
    'quick': 30,   # 30 minutes for quick-use seats
}
```

### Email Alerts

Add email notifications when seats exceed time limits:

```python
import smtplib
from email.mime.text import MIMEText

def send_alert(seat_id, duration):
    msg = MIMEText(f"Seat {seat_id} has been occupied for {duration}s")
    msg['Subject'] = 'Seat Occupancy Alert'
    msg['From'] = 'monitor@library.com'
    msg['To'] = 'admin@library.com'

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('your-email', 'your-password')
        server.send_message(msg)
```

### Data Logging

Log occupancy data to database for analytics:

```python
import sqlite3
from datetime import datetime

def log_occupancy(stats):
    conn = sqlite3.connect('occupancy.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO occupancy_logs (timestamp, total_seats, occupied_seats, available_seats)
        VALUES (?, ?, ?, ?)
    ''', (datetime.now(), stats['total_seats'], stats['occupied_seats'], stats['available_seats']))
    conn.commit()
    conn.close()
```

---

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/priyanshuharshbodhi1/Library-Seat-Occupancy-Detection/issues
- Email: asumansaree@gmail.com

---

## License

MIT License - See LICENSE file for details
