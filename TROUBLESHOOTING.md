# 🔧 Troubleshooting Guide

## Camera Issues

### Problem: "Failed to start webcam on camera 0"

#### Quick Fix:
```bash
# 1. Install OpenCV
pip install opencv-python opencv-python-headless

# 2. Test your camera
python test_camera.py

# 3. Restart the API server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Diagnosis Steps:

**Step 1: Test Camera with Diagnostic Tool**
```bash
python test_camera.py
```

This will:
- Check OpenCV installation
- Test cameras 0, 1, and 2
- Try different backends (DirectShow, MSMF)
- Show which cameras work

**Step 2: Use API Test Endpoint**
```bash
# Test camera 0
curl http://localhost:8000/api/webcam/test-camera?camera_index=0

# Test camera 1
curl http://localhost:8000/api/webcam/test-camera?camera_index=1
```

Or open in browser:
```
http://localhost:8000/api/webcam/test-camera?camera_index=0
```

**Step 3: Check Logs**

Look for detailed error messages in the terminal where the API is running.

---

## Common Issues & Solutions

### 1. Camera Not Detected

**Symptoms:**
- "Camera could not be opened"
- Test script shows no cameras found

**Solutions:**
✅ Check physical connection
✅ Try different USB ports
✅ Restart computer
✅ Check Device Manager (Windows)
✅ Update camera drivers

**Windows Settings:**
1. Open **Settings** > **Privacy** > **Camera**
2. Enable "Allow apps to access your camera"
3. Enable "Allow desktop apps to access your camera"

---

### 2. Camera In Use

**Symptoms:**
- Camera opens but can't read frames
- Works in other apps but not in this app

**Solutions:**
✅ Close other camera apps (Zoom, Teams, Skype, Discord)
✅ Close browser tabs using camera
✅ Restart the application
✅ Reboot computer

**Windows - Find apps using camera:**
```bash
# PowerShell
Get-Process | Where-Object {$_.ProcessName -like "*camera*"}
```

---

### 3. Wrong Camera Index

**Symptoms:**
- Camera starts but shows wrong camera
- Built-in laptop camera instead of external

**Solutions:**
✅ Try camera index 1 or 2
✅ Run test_camera.py to find correct index
✅ Disconnect other cameras
✅ Use the test endpoint to check each camera

---

### 4. Poor Detection Quality

**Symptoms:**
- No seats detected
- False detections
- Inconsistent tracking

**Solutions:**

**Improve Lighting:**
- Use bright, even lighting
- Avoid backlighting
- No shadows on seats

**Camera Position:**
- Position camera to see entire seating area
- Angle slightly downward
- Stable mounting (no shaking)

**Adjust Settings (.env):**
```bash
# Lower threshold for more detections
MODEL_CONF_THRESHOLD=0.3

# Higher threshold for fewer false positives
MODEL_CONF_THRESHOLD=0.5

# Adjust proximity matching
OCCUPANCY_PROXIMITY_THRESHOLD=80  # More precise
OCCUPANCY_PROXIMITY_THRESHOLD=150  # More flexible
```

---

### 5. Slow Performance

**Symptoms:**
- Laggy video
- Delayed updates
- Low FPS

**Solutions:**

**Use GPU:**
```bash
# .env file
MODEL_DEVICE=0  # Use first GPU
```

**Reduce Image Size:**
```bash
MODEL_IMG_SIZE=416  # Smaller, faster
```

**Increase Confidence:**
```bash
MODEL_CONF_THRESHOLD=0.5  # Process fewer detections
```

**Close Other Apps:**
- Close unnecessary browser tabs
- Stop other heavy applications
- Free up RAM

---

### 6. Web App Not Loading

**Symptoms:**
- Blank page
- 404 errors
- CSS/JS not loading

**Solutions:**
✅ Check API is running
✅ Hard refresh (Ctrl+F5)
✅ Clear browser cache
✅ Try different browser
✅ Check browser console (F12) for errors

**Verify Files Exist:**
```bash
ls static/
# Should see: app.html, css/, js/
```

---

### 7. Real-Time Updates Not Working

**Symptoms:**
- Seat map doesn't update
- Statistics frozen
- "Stopped" status but camera running

**Solutions:**
✅ Check browser console for JavaScript errors
✅ Ensure camera is started from Webcam Control page
✅ Hard refresh page (Ctrl+F5)
✅ Check network tab for failed API calls
✅ Restart API server

**Check API Endpoint:**
```bash
curl http://localhost:8000/api/webcam/occupancy
```

Should return JSON with seat data.

---

### 8. Model Loading Errors

**Symptoms:**
- "Model weights not found"
- "YOLO model error"

**Solutions:**
✅ Download model weights:
```bash
python download_models.py
```

✅ Or manually:
```bash
wget https://github.com/WongKinYiu/yolov7/releases/download/v0.1/yolov7.pt
```

✅ Verify file exists:
```bash
ls yolov7.pt
# Should show file size ~74MB
```

---

### 9. NumPy/Torch Compatibility

**Symptoms:**
- "module 'numpy' has no attribute"
- "RuntimeError: CUDA error"

**Solutions:**

**NumPy 2.x Issues:**
```bash
pip install "numpy<2.0"
```

**Torch CUDA Issues:**
```bash
# CPU only version
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Or with CUDA 11.7
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu117
```

---

### 10. Port Already in Use

**Symptoms:**
- "Address already in use"
- Can't start server

**Solutions:**

**Windows:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

**Or use different port:**
```bash
# .env file
API_PORT=8001

# Then access at http://localhost:8001
```

---

## Advanced Diagnostics

### Check All Dependencies

```bash
pip list | grep -E "opencv|torch|numpy|fastapi|uvicorn"
```

Should show:
- opencv-python: 4.x
- torch: 2.x
- numpy: 1.x or 2.x
- fastapi: 0.1x
- uvicorn: 0.x

### Test Model Loading

```python
# test_model.py
import torch
from models.experimental import attempt_load

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = attempt_load('yolov7.pt', map_location=device)
print(f"Model loaded on {device}")
print(f"Model names: {model.names}")
```

### Test API Directly

```bash
# Health check
curl http://localhost:8000/health

# Camera status
curl http://localhost:8000/api/webcam/status

# Test camera
curl http://localhost:8000/api/webcam/test-camera?camera_index=0
```

### Check Logs

```bash
# API logs
tail -f api/logs/app.log

# Or run with verbose logging
LOG_LEVEL=DEBUG python -m uvicorn api.main:app --reload
```

---

## Quick Fixes Summary

| Issue | Quick Fix |
|-------|-----------|
| Camera not found | `python test_camera.py` |
| OpenCV missing | `pip install opencv-python` |
| Slow performance | Set `MODEL_DEVICE=0` in .env |
| Port in use | Use `API_PORT=8001` in .env |
| Model not found | `python download_models.py` |
| App not loading | Hard refresh (Ctrl+F5) |
| Updates frozen | Restart API server |
| Bad detection | Improve lighting, lower threshold |

---

## Getting Help

### Log Collection

When reporting issues, include:

1. **Camera Test Output:**
   ```bash
   python test_camera.py > camera_test.log 2>&1
   ```

2. **API Logs:**
   ```bash
   # Terminal output where API is running
   ```

3. **Browser Console:**
   - Press F12
   - Go to Console tab
   - Copy any errors

4. **System Info:**
   ```bash
   python --version
   pip list > requirements_installed.txt
   ```

### Useful Commands

```bash
# Full diagnostic
python test_camera.py
curl http://localhost:8000/health
curl http://localhost:8000/api/webcam/test-camera?camera_index=0

# Check processes
tasklist | findstr python  # Windows
ps aux | grep python       # Linux/Mac

# Network check
netstat -an | findstr 8000  # Windows
netstat -an | grep 8000     # Linux/Mac
```

---

## Contact & Support

- **GitHub Issues**: Report bugs and request features
- **Documentation**: See README.md, WEBAPP_GUIDE.md
- **API Docs**: http://localhost:8000/docs
- **Test Endpoint**: http://localhost:8000/api/webcam/test-camera

---

## Prevention Tips

1. **Regular Updates:**
   ```bash
   pip install --upgrade opencv-python torch fastapi uvicorn
   ```

2. **Clean Restarts:**
   - Stop API server properly (Ctrl+C)
   - Release camera resources
   - Restart when making changes

3. **Monitor Resources:**
   - Check CPU/RAM usage
   - Close unnecessary applications
   - Use Task Manager to monitor

4. **Regular Testing:**
   - Run test_camera.py weekly
   - Check API health endpoint
   - Monitor log files for warnings

---

**Remember:** Most issues are related to:
1. Camera permissions/access
2. Missing dependencies
3. Port conflicts
4. Incorrect configuration

Run the diagnostic tools first before deeper troubleshooting!
