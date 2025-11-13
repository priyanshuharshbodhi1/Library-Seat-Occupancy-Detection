# Real-Time Seat Occupancy Detection - Complete Feature Guide

## What's New? 🎉

Your Library Seat Occupancy Detection system now includes **full real-time webcam monitoring** with a beautiful web dashboard!

### Key Improvements

1. **✅ Fixed API Issues**
   - Fixed Windows Unicode encoding errors
   - Updated API dependencies
   - Improved error handling

2. **🎥 Real-Time Webcam Detection**
   - Live camera feed processing
   - Real-time person and chair detection
   - Continuous occupancy tracking

3. **📊 Live Web Dashboard**
   - Beautiful, responsive UI
   - Real-time statistics
   - Individual seat monitoring
   - Time exceeded alerts

4. **🔌 RESTful API**
   - Complete webcam control endpoints
   - Real-time data streaming
   - MJPEG video stream
   - Occupancy statistics API

---

## Quick Start Guide

### Step 1: Install Dependencies

```bash
# Install API requirements
pip install -r requirements-api.txt

# Install detection requirements (if not already installed)
pip install -r requirements.txt
```

### Step 2: Start the System

#### Option A: Using Startup Script (Easiest)
```bash
# On Windows
start_webcam_monitor.bat

# On Linux/Mac
chmod +x start_webcam_monitor.sh
./start_webcam_monitor.sh
```

#### Option B: Manual Start
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Open Dashboard

Open your browser and go to:
```
http://localhost:8000
```

### Step 4: Start Monitoring

1. Select your camera (default is 0)
2. Click **"Start Camera"**
3. Point your webcam at the seating area
4. Watch the magic happen! ✨

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Browser                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Real-Time Dashboard (index.html)            │    │
│  │  • Live video stream                                │    │
│  │  • Occupancy statistics                             │    │
│  │  • Seat status monitoring                           │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/WebSocket
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Server (api/main.py)             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Webcam Routes (api/routes/webcam.py)                │  │
│  │  • POST /api/webcam/start                            │  │
│  │  • POST /api/webcam/stop                             │  │
│  │  • GET  /api/webcam/stream  (MJPEG)                  │  │
│  │  • GET  /api/webcam/occupancy                        │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│          Webcam Service (api/services/webcam_service.py)    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  WebcamDetector Class                                │  │
│  │  • Captures frames from webcam                       │  │
│  │  • Processes with YOLOv7 model                       │  │
│  │  • Tracks seats with SORT algorithm                  │  │
│  │  • Monitors occupancy duration                       │  │
│  │  • Generates statistics                              │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
              ┌────────────────┐
              │   Your Webcam  │
              └────────────────┘
```

---

## File Structure

### New Files Created

```
Library-Seat-Occupancy-Detection/
├── api/
│   ├── routes/
│   │   └── webcam.py                    # NEW: Webcam API endpoints
│   └── services/
│       └── webcam_service.py            # NEW: Real-time detection service
├── static/
│   └── index.html                       # NEW: Web dashboard
├── WEBCAM_GUIDE.md                      # NEW: Detailed usage guide
├── REALTIME_FEATURES.md                 # NEW: This file
├── start_webcam_monitor.bat             # NEW: Windows startup script
└── start_webcam_monitor.sh              # NEW: Linux/Mac startup script
```

### Modified Files

```
api/
├── main.py                              # Added webcam routes & static files
└── run_api.py                           # Fixed Windows Unicode encoding
```

---

## Features Comparison

### Before (Video Upload Mode)
- Upload pre-recorded video
- Wait for processing
- Download results
- No real-time feedback

### After (Real-Time Webcam Mode)
- ✅ Live webcam feed
- ✅ Instant detection and tracking
- ✅ Real-time statistics
- ✅ Immediate alerts
- ✅ Beautiful web dashboard
- ✅ Multi-camera support
- ✅ Plus all original features still work!

---

## API Endpoints Summary

### Webcam Control

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/webcam/start` | POST | Start webcam detection |
| `/api/webcam/stop` | POST | Stop webcam detection |
| `/api/webcam/status` | GET | Get webcam status |
| `/api/webcam/stream` | GET | MJPEG video stream |
| `/api/webcam/occupancy` | GET | Get real-time occupancy data |

### Original Video Processing (Still Available)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/detect` | POST | Upload video for processing |
| `/api/jobs/{job_id}` | GET | Get job status |
| `/api/download/{job_id}` | GET | Download processed video |
| `/api/jobs` | GET | List all jobs |

### System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web dashboard |
| `/health` | GET | Health check |
| `/docs` | GET | API documentation |

---

## Configuration Options

Edit `.env` file to customize:

```bash
# Model Settings
MODEL_CONF_THRESHOLD=0.4           # Detection confidence (lower = more detections)
MODEL_IOU_THRESHOLD=0.45           # Overlap threshold
MODEL_DEVICE=                      # '' = auto, '0' = GPU, 'cpu' = CPU only

# Occupancy Settings
OCCUPANCY_TIME_THRESHOLD=10        # Seconds before "TIME EXCEEDED" warning
OCCUPANCY_PROXIMITY_THRESHOLD=100  # Pixels for seat matching

# API Settings
API_PORT=8000                      # Server port
CORS_ENABLED=True                  # Enable cross-origin requests
DEBUG=True                         # Debug mode
```

---

## Dashboard Features

### Live Video Feed
- Real-time video with bounding boxes
- Color-coded indicators:
  - 🟢 Green = Available seats
  - 🔴 Red = Occupied seats
  - Person detection overlay

### Statistics Cards
- **Total Seats**: Detected seat count
- **Available**: Currently available seats
- **Occupied**: Currently occupied seats
- **People Detected**: Real-time person count

### Individual Seat Monitoring
- Seat ID
- Status (Available/Occupied)
- Duration (time occupied)
- ⚠️ TIME EXCEEDED alerts
- Real-time updates every second

### Controls
- Camera selection dropdown
- Start/Stop buttons
- Status indicator

---

## Use Case Examples

### 1. Library Management
```
Monitor 50+ seats in real-time
Display availability on screens
Track usage patterns
Optimize space allocation
```

### 2. Co-Working Spaces
```
Real-time desk availability
Hot-desking management
Usage analytics
Member notifications
```

### 3. Cafeteria/Restaurant
```
Table availability tracking
Turnover time monitoring
Peak hour analysis
Queue management
```

### 4. Study Halls
```
Occupancy monitoring
Time limit enforcement
Space optimization
Student notifications
```

---

## Integration Examples

### Digital Signage Display
```python
import requests
from time import sleep

while True:
    response = requests.get("http://localhost:8000/api/webcam/occupancy")
    data = response.json()

    if data['status'] == 'running':
        stats = data['data']
        print(f"\n{'='*40}")
        print(f"LIBRARY SEAT AVAILABILITY")
        print(f"{'='*40}")
        print(f"Available Seats: {stats['available_seats']}")
        print(f"Total Seats: {stats['total_seats']}")
        print(f"Occupancy: {(stats['occupied_seats']/stats['total_seats']*100):.1f}%")

    sleep(5)
```

### Mobile App Integration
```javascript
// React Native example
const fetchOccupancy = async () => {
  try {
    const response = await fetch('http://your-server:8000/api/webcam/occupancy');
    const data = await response.json();

    if (data.status === 'running') {
      setAvailableSeats(data.data.available_seats);
      setTotalSeats(data.data.total_seats);
    }
  } catch (error) {
    console.error('Error fetching occupancy:', error);
  }
};

useEffect(() => {
  const interval = setInterval(fetchOccupancy, 1000);
  return () => clearInterval(interval);
}, []);
```

### Slack/Discord Notifications
```python
import requests
from datetime import datetime

def check_and_notify():
    response = requests.get("http://localhost:8000/api/webcam/occupancy")
    data = response.json()

    if data['status'] == 'running':
        stats = data['data']

        # Alert if seats are available
        if stats['available_seats'] > 0:
            webhook_url = "YOUR_SLACK_WEBHOOK_URL"
            message = {
                "text": f"📚 {stats['available_seats']} seats now available! (as of {datetime.now().strftime('%I:%M %p')})"
            }
            requests.post(webhook_url, json=message)
```

---

## Troubleshooting

### Common Issues

**1. API won't start**
- Check if port 8000 is already in use
- Try: `netstat -ano | findstr :8000`
- Kill the process or use a different port

**2. Camera not detected**
- Try different camera indices (0, 1, 2)
- Check camera permissions
- Close other apps using the camera

**3. Slow performance**
- Use GPU: `MODEL_DEVICE=0`
- Reduce image size: `MODEL_IMG_SIZE=416`
- Increase threshold: `MODEL_CONF_THRESHOLD=0.5`

**4. No seats detected**
- Ensure chairs are visible
- Improve lighting
- Lower threshold: `MODEL_CONF_THRESHOLD=0.3`

**5. Frontend not loading**
- Check if API is running
- Clear browser cache
- Check browser console (F12) for errors

---

## Performance Tips

### For Accuracy
- Use good lighting
- Position camera to show entire seating area
- Minimize camera movement
- Use higher confidence threshold

### For Speed
- Use GPU if available
- Reduce image size
- Increase confidence threshold
- Process every other frame

---

## Security Best Practices

1. **Change Default Settings**
   ```bash
   API_KEY_ENABLED=True
   API_KEY=your-secure-random-key-here
   ```

2. **Use HTTPS in Production**
   ```bash
   # Use nginx or similar reverse proxy
   ```

3. **Restrict CORS Origins**
   ```bash
   CORS_ORIGINS=https://yourdomain.com
   ```

4. **Network Security**
   - Use firewall rules
   - VPN for remote access
   - Monitor access logs

---

## Next Steps

### Suggested Enhancements

1. **Database Integration**
   - Log occupancy data
   - Generate reports
   - Track trends

2. **Email/SMS Alerts**
   - Notify when seats available
   - Alert on time exceeded
   - Daily summaries

3. **Mobile App**
   - Native iOS/Android app
   - Push notifications
   - Seat reservations

4. **Advanced Analytics**
   - Peak usage times
   - Average occupancy duration
   - Heat maps

5. **Multi-Location Support**
   - Monitor multiple rooms
   - Centralized dashboard
   - Location-based stats

---

## Support & Resources

- **Documentation**: See `WEBCAM_GUIDE.md` for detailed usage
- **API Docs**: http://localhost:8000/docs
- **GitHub**: https://github.com/priyanshuharshbodhi1/Library-Seat-Occupancy-Detection
- **Issues**: Report bugs on GitHub Issues

---

## Credits

- **YOLOv7**: Object detection model
- **SORT**: Multi-object tracking
- **FastAPI**: Modern web framework
- **OpenCV**: Computer vision library

---

## License

MIT License - Feel free to use, modify, and distribute!

---

**Enjoy your new real-time seat monitoring system! 🎉**

For questions or support, open an issue on GitHub or email: asumansaree@gmail.com
