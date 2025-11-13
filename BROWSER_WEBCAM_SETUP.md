# 🎥 Browser-Based Webcam Setup Guide

## Why This Change?

**Problem**: Backend (Docker/Server) can't access your local webcam
**Solution**: Capture video in browser, send frames to backend for processing

## Architecture

```
Browser (Your Computer)          Backend (Server/Docker)
    ↓                                    ↓
[Webcam Access]  ───frames→   [YOLOv7 Processing]
    ↓                                    ↓
[Display Results] ←──detection─  [Return Results]
```

## Quick Start

### Step 1: Copy the New JavaScript

Replace `static/js/app.js` with the browser-based version at:
`static/js/app-browser.js`

```bash
cp static/js/app-browser.js static/js/app.js
```

###Step 2: Start Server

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Test It

1. Open http://localhost:8000
2. Click "Start Camera"
3. **Allow camera permission popup**
4. Watch detections happen!

## How It Works

### 1. Browser Requests Camera Permission

```javascript
// Triggers browser permission popup
const stream = await navigator.mediaDevices.getUserMedia({
    video: { width: 1280, height: 720 }
});
```

**You'll see**: Browser popup asking "Allow camera access?"
**Click**: "Allow"

### 2. Browser Captures Frames

```javascript
// Every 1 second
setInterval(() => {
    // Capture frame from <video>
    canvas.drawImage(videoElement, 0, 0);

    // Convert to JPEG
    const frameData = canvas.toDataURL('image/jpeg');

    // Send to backend
    fetch('/api/process/frame', {
        method: 'POST',
        body: frameData
    });
}, 1000);
```

### 3. Backend Processes Frame

```python
# api/routes/webcam_browser.py
@router.post("/frame")
async def process_frame(frame_data: str):
    # Decode base64 image
    image = base64.b64decode(frame_data)

    # Run YOLO detection
    results = detector.process(image)

    # Return detections
    return {
        "detections": [...],
        "occupancy": {...}
    }
```

### 4. Browser Updates UI

```javascript
// Receive results
const result = await response.json();

// Update seat map
updateSeatMap(result.occupancy.seats);

// Draw bounding boxes
drawBoxes(result.detections);
```

## API Endpoints

### New Endpoints (Browser-Based)

```
POST /api/process/frame
  - Accepts: Base64 image
  - Returns: Detections + occupancy stats

POST /api/process/frame-binary
  - Accepts: Binary image file
  - Returns: Detections + occupancy stats

GET /api/process/stats
  - Returns: Current occupancy stats

POST /api/process/reset
  - Resets all tracking
```

### Old Endpoints (Server-Based - Still Work)

```
POST /api/webcam/start  - Won't work in Docker
POST /api/webcam/stop   - Won't work in Docker
GET /api/webcam/stream  - Won't work in Docker
```

## Testing

### Test Browser Camera Access

Open browser console (F12) and run:

```javascript
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => console.log('✅ Camera works!', stream))
    .catch(err => console.error('❌ Error:', err));
```

### Test Backend Processing

```bash
# Test with a sample image
curl -X POST "http://localhost:8000/api/process/frame-binary" \
  -F "frame=@test_image.jpg"
```

## Troubleshooting

### Camera Permission Not Showing

**Cause**: HTTPS required for camera access (except localhost)

**Solution**:
- ✅ Works on `localhost` (HTTP OK)
- ✅ Works on `127.0.0.1` (HTTP OK)
- ❌ Doesn't work on `192.168.x.x` (needs HTTPS)
- ❌ Doesn't work on domain (needs HTTPS)

**For production**: Use HTTPS/SSL

### Permission Denied

**Cause**: User clicked "Block" or camera blocked in settings

**Solutions**:
1. Click the camera icon in address bar
2. Change permission to "Allow"
3. Refresh page

**Chrome**: `chrome://settings/content/camera`
**Firefox**: Settings → Privacy & Security → Permissions → Camera

### Camera Already in Use

**Cause**: Another app/tab using camera

**Solutions**:
1. Close other apps (Zoom, Teams, Skype)
2. Close other browser tabs
3. Restart browser

### No Detections

**Cause**: Poor lighting, wrong camera angle

**Solutions**:
1. Improve lighting
2. Position camera to show seats
3. Lower confidence threshold in `.env`:
   ```
   MODEL_CONF_THRESHOLD=0.3
   ```

### Slow Performance

**Cause**: Processing too many frames

**Solutions**:
1. Increase interval (currently 1 second):
   ```javascript
   setInterval(processFrame, 2000); // 2 seconds
   ```

2. Use GPU:
   ```
   MODEL_DEVICE=0
   ```

3. Reduce image quality:
   ```javascript
   canvas.toDataURL('image/jpeg', 0.5); // Lower quality
   ```

## Browser Compatibility

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome 90+ | ✅ Full | Recommended |
| Firefox 88+ | ✅ Full | Recommended |
| Safari 14+ | ✅ Full | May need HTTPS |
| Edge 90+ | ✅ Full | Chromium-based |
| Opera 76+ | ✅ Full | Chromium-based |
| IE 11 | ❌ No | Not supported |

## Production Deployment

### Enable HTTPS

For production (not localhost), you need HTTPS:

**Option 1: Nginx Reverse Proxy**

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
    }
}
```

**Option 2: Let's Encrypt**

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com
```

**Option 3: Cloudflare**

Use Cloudflare for free SSL/HTTPS

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./yolov7.pt:/app/yolov7.pt
    environment:
      - MODEL_DEVICE=0  # Use GPU if available
```

**Important**: Browser accesses camera, not Docker container!

## Security Considerations

### 1. Camera Privacy

**What Users See**:
- Browser popup: "Allow camera?"
- Camera indicator light (hardware)
- Browser tab shows camera icon

**Users Can**:
- Deny permission
- Revoke permission anytime
- See which sites have camera access

### 2. Data Privacy

**What's Sent to Server**:
- Image frames (1 per second)
- No video recording
- No audio

**What's NOT Sent**:
- Continuous video stream
- Personal information
- Audio data

**Server Processing**:
- Processes frame
- Detects objects
- Returns results
- **Doesn't store images**

### 3. Best Practices

```javascript
// Add to your app.js
const PRIVACY_NOTICE = `
This application uses your camera to detect seat occupancy.
- Images are sent to the server for processing
- No images are stored or recorded
- You can stop anytime by clicking "Stop Camera"
- Camera access can be revoked in browser settings
`;

// Show before requesting camera
if (confirm(PRIVACY_NOTICE + '\n\nAllow camera access?')) {
    startCamera();
}
```

## Performance Optimization

### Frame Rate

```javascript
// High accuracy (slow)
setInterval(processFrame, 500);  // 2 FPS

// Balanced (recommended)
setInterval(processFrame, 1000); // 1 FPS

// Low bandwidth (fast)
setInterval(processFrame, 2000); // 0.5 FPS
```

### Image Quality

```javascript
// High quality (larger file)
canvas.toDataURL('image/jpeg', 1.0);

// Balanced (recommended)
canvas.toDataURL('image/jpeg', 0.8);

// Low quality (smaller file)
canvas.toDataURL('image/jpeg', 0.5);
```

### Image Size

```javascript
// Full size (slow)
canvas.width = video.videoWidth;
canvas.height = video.videoHeight;

// Scaled down (faster)
canvas.width = 640;
canvas.height = 480;
```

## Complete Example

```html
<!DOCTYPE html>
<html>
<body>
    <video id="video" autoplay></video>
    <canvas id="canvas"></canvas>
    <button onclick="start()">Start</button>

    <script>
    let stream, video, canvas, ctx, interval;

    async function start() {
        // 1. Get camera
        stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 1280, height: 720 }
        });

        // 2. Show video
        video = document.getElementById('video');
        video.srcObject = stream;

        // 3. Setup canvas
        canvas = document.getElementById('canvas');
        ctx = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        // 4. Start processing (1 FPS)
        interval = setInterval(async () => {
            // Capture frame
            ctx.drawImage(video, 0, 0);
            const frameData = canvas.toDataURL('image/jpeg', 0.8);

            // Send to backend
            const formData = new FormData();
            formData.append('frame_data', frameData);

            const response = await fetch('/api/process/frame', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            console.log('Detections:', result);

            // Update UI
            updateUI(result);
        }, 1000);
    }

    function updateUI(result) {
        // Draw boxes, update seat map, etc.
    }
    </script>
</body>
</html>
```

## Summary

### Before (Server-Based)
- ❌ Backend captures webcam
- ❌ Doesn't work in Docker
- ❌ Can't access local camera from server
- ✅ Works only on local machine

### After (Browser-Based)
- ✅ Browser captures webcam
- ✅ Works with Docker/server
- ✅ Accesses local camera from browser
- ✅ Works on any deployment
- ✅ User sees permission popup
- ✅ More secure and private

## Next Steps

1. Copy app-browser.js to app.js
2. Restart server
3. Open browser
4. Click "Start Camera"
5. Allow permission
6. Watch magic happen!

## Support

- Check browser console for errors (F12)
- Test camera: `navigator.mediaDevices.getUserMedia({video:true})`
- Test API: http://localhost:8000/docs
- Check logs: Terminal where server is running

---

**Ready! Your system now works with Docker and any deployment! 🎉**
