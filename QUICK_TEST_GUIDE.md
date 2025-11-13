# Quick Test Guide - Browser-Based Webcam Detection

## What's Been Fixed

✅ **Complete browser-based webcam capture implementation**
- Frontend captures video using browser's getUserMedia API
- Frames sent to backend for YOLO processing every 1 second
- Real-time seat detection and occupancy tracking
- Multi-page GUI with seat map and analytics

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Browser (Your Computer)                         │
│  - Captures webcam via getUserMedia()            │
│  - Triggers permission popup                     │
│  - Sends frames every 1 second                   │
└────────────────┬────────────────────────────────┘
                 │
                 │ POST /api/process/frame
                 │ (Base64 JPEG frame)
                 ↓
┌─────────────────────────────────────────────────┐
│  Backend (Docker/Server)                         │
│  - Receives frame from browser                   │
│  - Runs YOLOv7 detection                         │
│  - SORT tracking for seat management             │
│  - Returns detection results                     │
└────────────────┬────────────────────────────────┘
                 │
                 │ JSON response
                 │ {occupancy, detections}
                 ↓
┌─────────────────────────────────────────────────┐
│  Browser UI                                      │
│  - Updates stats display                         │
│  - Draws bounding boxes                          │
│  - Updates seat map (movie-style grid)           │
│  - Shows analytics                               │
└─────────────────────────────────────────────────┘
```

## Files Modified/Created

### Modified:
- `api/main.py` - Added webcam_browser routes (line 93)
- `static/js/app.js` - **COMPLETED** with all helper functions
- `static/js/app-browser.js` - **COMPLETED** (same as app.js)

### Already Created (from previous work):
- `api/routes/webcam_browser.py` - Browser frame processing endpoints
- `api/services/frame_processor.py` - YOLOv7 + SORT processing
- `static/app.html` - Multi-page web interface
- `static/css/styles.css` - Complete styling

## Testing Steps

### 1. Start the Server

```bash
python run_api.py
```

Or using uvicorn directly:

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Open the Web App

Open your browser and navigate to:
```
http://localhost:8000
```

### 3. Test Camera Permission Popup

1. Click the **"Start Camera"** button
2. **You should see a browser permission popup** asking:
   ```
   http://localhost:8000 wants to use your camera
   [Block] [Allow]
   ```
3. Click **"Allow"**

**This is the key test** - if you see this popup, the browser-based capture is working!

### 4. Verify Video Capture

After allowing camera access:
- Video feed should appear in the video container
- Status should change to "Camera Running" (green)
- Activity log should show "Camera started successfully"

### 5. Verify Backend Processing

Watch the **terminal/console** where the server is running:
```
INFO: Processing frame...
INFO: Detected 2 persons, 3 chairs
INFO: Tracked 3 seats
```

### 6. Check Real-Time Updates

On the web interface, you should see updates **every 1 second**:
- **Live Statistics** cards updating
- **Available/Occupied** seat counts changing
- **Activity log** showing new entries

### 7. Test Seat Map Page

1. Click **"Seat Map"** in the navigation
2. Should see a grid of seats (movie-style booking interface)
3. Colors:
   - 🟢 **Green** = Available seat
   - 🔴 **Red** = Occupied seat
   - 🟠 **Orange** = Time exceeded

### 8. Test Analytics Page

1. Click **"Analytics"** in the navigation
2. Should see:
   - Occupancy percentage bar
   - Average duration
   - Peak usage time
   - Detailed seat table

## Browser Compatibility Test

### Supported Browsers:
- ✅ Chrome 90+ (Recommended)
- ✅ Firefox 88+
- ✅ Edge 90+
- ✅ Safari 14+

### Test in Different Browsers:
```
Chrome: http://localhost:8000
Firefox: http://localhost:8000
Edge: http://localhost:8000
```

## API Endpoint Tests

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-14T..."
}
```

### Test 2: Process Stats
```bash
curl http://localhost:8000/api/process/stats
```

**Expected:**
```json
{
  "success": true,
  "occupancy": {
    "total_seats": 0,
    "occupied_seats": 0,
    "available_seats": 0,
    ...
  }
}
```

### Test 3: Browser Console Test

Open browser console (F12) and run:

```javascript
// Test 1: Check camera access
navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => {
    console.log('✅ Camera access works!', stream);
    stream.getTracks().forEach(track => track.stop()); // Stop test stream
  })
  .catch(err => console.error('❌ Camera error:', err));

// Test 2: Test backend API
fetch('/api/process/stats')
  .then(res => res.json())
  .then(data => console.log('✅ Backend API works:', data))
  .catch(err => console.error('❌ API error:', err));
```

## Expected Behavior

### When Starting Camera:

1. **Button state changes**: "Start Camera" → "Starting..." → disabled
2. **Permission popup appears** (THIS IS KEY!)
3. **User clicks "Allow"**
4. **Video feed appears**
5. **Status badge**: "Camera Stopped" → "Camera Running" (green)
6. **Console logs**: "Requesting camera access..." → "Camera access granted!" → "Video playing"
7. **Activity log**: "Camera started successfully"
8. **Frame processing starts** (1 frame per second)

### During Processing:

- Stats update every 1 second
- Bounding boxes appear on video (if detections found)
- Activity log shows seat changes
- Seat map updates in real-time
- Analytics page shows current metrics

### When Stopping Camera:

1. **Button state**: "Stop Camera" → "Stopping..." → disabled
2. **Video stops**
3. **Camera light turns off** (hardware indicator)
4. **Status**: "Camera Running" → "Camera Stopped"
5. **Stats reset to 0**
6. **Placeholder appears**: "Click Start Camera to begin monitoring"

## Troubleshooting

### Issue 1: No Permission Popup

**Cause**: Camera already blocked or using wrong URL

**Fix**:
- Click camera icon in browser address bar
- Change to "Allow"
- Refresh page
- Ensure using `http://localhost:8000` (not IP address)

### Issue 2: "Permission Denied" Error

**Cause**: User clicked "Block"

**Fix**:
- Chrome: `chrome://settings/content/camera`
- Firefox: Settings → Privacy & Security → Permissions → Camera
- Remove block for `http://localhost:8000`
- Refresh page

### Issue 3: Camera Light On, No Video

**Cause**: Another app using camera

**Fix**:
- Close Zoom, Teams, Skype, etc.
- Close other browser tabs
- Restart browser

### Issue 4: Server Error 500

**Check server logs** for:
- `ModuleNotFoundError: No module named 'cv2'` → Run `pip install opencv-python`
- Model loading errors → Check `yolov7.pt` file exists
- CUDA errors → Set `MODEL_DEVICE=cpu` in `.env`

### Issue 5: No Detections

**Cause**: Poor lighting or camera angle

**Fix**:
- Point camera at seating area
- Improve lighting
- Lower threshold: `MODEL_CONF_THRESHOLD=0.3` in `.env`
- Check console for detection logs

### Issue 6: Stats Not Updating

**Check browser console (F12)** for:
- Network errors (red in Network tab)
- JavaScript errors
- API response errors

**Fix**:
- Verify backend is running
- Check `/api/process/frame` endpoint responds
- Ensure no CORS errors

## Performance Notes

### Frame Rate:
- Default: 1 FPS (1 frame per second)
- Adjustable in `app.js` line 250: `setInterval(processFrame, 1000)`
- Faster: `setInterval(processFrame, 500)` = 2 FPS
- Slower: `setInterval(processFrame, 2000)` = 0.5 FPS

### Image Quality:
- Default: 0.8 quality (80%)
- Adjustable in `app.js` line 277: `toDataURL('image/jpeg', 0.8)`
- Higher quality: `0.9` (larger file, slower)
- Lower quality: `0.5` (smaller file, faster)

## Success Criteria

✅ **Camera permission popup appears**
✅ **Video feed displays in browser**
✅ **Stats update every 1 second**
✅ **Seat map shows colored seats**
✅ **Activity log shows real-time events**
✅ **No console errors**
✅ **Server processes frames successfully**
✅ **Works with Docker/remote deployment**

## Next Steps

If all tests pass:

1. **Test with actual seating area**:
   - Position camera to view chairs
   - Ensure good lighting
   - Watch detections appear

2. **Test seat tracking**:
   - Sit in a chair
   - Verify seat changes to "occupied" (red)
   - Stand up
   - Verify seat changes to "available" (green)

3. **Test duration tracking**:
   - Occupy a seat for 2+ minutes
   - Check analytics page for duration
   - Verify time exceeded warning (orange) after threshold

4. **Deploy to production**:
   - Use HTTPS for remote access
   - Configure camera angles
   - Set appropriate confidence thresholds

## Support

If issues persist:

1. Check browser console (F12) for errors
2. Check server logs for backend errors
3. Review `BROWSER_WEBCAM_SETUP.md` for detailed architecture
4. Test API endpoints individually
5. Verify camera works in other apps

---

## Summary

The browser-based webcam capture system is **complete and ready to test**:

- ✅ Frontend captures webcam (triggers permission popup)
- ✅ Sends frames to backend every 1 second
- ✅ Backend processes with YOLOv7 + SORT
- ✅ Real-time UI updates (stats, seat map, analytics)
- ✅ Works with Docker deployment
- ✅ Multi-page GUI interface
- ✅ Movie-style seat visualization

**Start testing now by running the server and opening http://localhost:8000!**
