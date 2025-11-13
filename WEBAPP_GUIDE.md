# 🎯 Multi-Page Web Application User Guide

## Overview

Your Library Seat Occupancy Detection system now features a **professional multi-page web application** with:
- 📹 **Webcam Control Page** - Start/stop camera and view live feed
- 🎭 **Visual Seat Map** - Real-time seat visualization (like movie ticket booking)
- 📊 **Analytics Dashboard** - Statistics and insights
- ⚡ **Real-time Updates** - 1-second refresh intervals
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

---

## Quick Start

### Step 1: Start the Server

```bash
# Windows
start_webcam_monitor.bat

# Linux/Mac
./start_webcam_monitor.sh

# Or manually
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 2: Open the Web App

Open your browser and navigate to:
```
http://localhost:8000
```

### Step 3: Start Monitoring

1. Click **"Webcam Control"** in the navigation
2. Select your camera (default is Camera 0)
3. Click **"Start Camera"**
4. Navigate to **"Seat Map"** to see visual representation
5. Check **"Analytics"** for statistics

---

## Application Features

### 🏠 Navigation Bar

The top navigation bar allows you to switch between three main pages:

1. **📹 Webcam Control** - Camera controls and live video
2. **🎭 Seat Map** - Visual grid of all seats
3. **📊 Analytics** - Statistics and insights

Click any tab to navigate between pages.

---

## Page Descriptions

### 1. 📹 Webcam Control Page

**Purpose**: Control the webcam and view live detection feed

#### Features:

**Status Indicator**
- 🟢 Green badge: Camera running
- 🔴 Red badge: Camera stopped

**Camera Selector**
- Dropdown to choose camera (0, 1, 2)
- Default: Camera 0

**Control Buttons**
- **Start Camera**: Begin detection
- **Stop Camera**: End detection

**Live Video Feed**
- Real-time camera stream
- Bounding boxes on detected persons/chairs
- Occupancy status overlays

**Live Statistics Cards**
- 📊 Total Seats
- ✅ Available Seats
- 🔴 Occupied Seats
- 👥 People Detected

**Activity Feed**
- Recent events log
- Timestamps for all actions
- Seat changes and alerts

#### How to Use:

1. Select your camera from dropdown
2. Click **"Start Camera"**
3. Point camera at seating area
4. Watch live detection and statistics
5. Monitor activity feed for changes

---

### 2. 🎭 Seat Map Page

**Purpose**: Visual representation of all seats (like movie ticket booking)

#### Features:

**Legend**
- 🟢 Green boxes: Available seats
- 🔴 Red boxes: Occupied seats
- 🟠 Orange boxes: Time exceeded

**Statistics Bar**
- Total seats count
- Available seats (green)
- Occupied seats (red)

**Seat Grid**
- Each seat shown as a colored box
- Seat number displayed
- Status text (Free/Busy/Exceeded)
- Duration timer for occupied seats
- Hover for details

#### Visual Layout:

```
┌─────────────────────────────────────────┐
│  Legend: 🟢 Available  🔴 Busy  🟠 Alert │
├─────────────────────────────────────────┤
│  Total: 12  Available: 7  Occupied: 5   │
├─────────────────────────────────────────┤
│                                         │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ │
│  │ 1 │ │ 2 │ │ 3 │ │ 4 │ │ 5 │ │ 6 │ │
│  │ 🟢 │ │ 🔴 │ │ 🟢 │ │ 🔴 │ │ 🟢 │ │ 🟠 │ │
│  │Free│ │Busy│ │Free│ │Busy│ │Free│ │>10m│ │
│  └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ │
│                                         │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ │
│  │ 7 │ │ 8 │ │ 9 │ │10 │ │11 │ │12 │ │
│  │ 🟢 │ │ 🟢 │ │ 🔴 │ │ 🟢 │ │ 🔴 │ │ 🟢 │ │
│  │Free│ │Free│ │Busy│ │Free│ │Busy│ │Free│ │
│  └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ │
│                                         │
└─────────────────────────────────────────┘
```

#### How to Use:

1. Navigate to **"Seat Map"** tab
2. Ensure camera is running
3. View real-time seat status
4. Green = available, Red = occupied
5. Orange with pulsing animation = time exceeded
6. Hover over any seat for details
7. Watch as status updates every second

**Seat Status Changes:**
- Automatically updates every **1 second**
- Color changes instantly
- Duration timer updates in real-time
- Smooth animations

---

### 3. 📊 Analytics Page

**Purpose**: View statistics and insights about seat usage

#### Features:

**Occupancy Rate Meter**
- Visual bar showing occupancy percentage
- Color gradient: Green → Yellow → Red
- Real-time percentage display

**Average Duration**
- Average time seats are occupied
- Displayed in minutes:seconds format

**Peak Usage Time**
- Time when occupancy was highest
- Updates when > 50% occupied

**Detailed Seat List**
- All seats with individual status
- Occupancy duration for each
- Time exceeded warnings
- Scrollable list

#### How to Use:

1. Navigate to **"Analytics"** tab
2. View occupancy rate meter
3. Check average duration
4. Review detailed seat list
5. Identify seats exceeding time limits

---

## Real-Time Features

### ⚡ 1-Second Updates

The application updates **every 1 second** automatically:

**What Updates:**
- Statistics (total, occupied, available)
- Seat map colors and status
- Duration timers
- Activity log
- Analytics metrics

**How It Works:**
- API polls `/api/webcam/occupancy` every 1000ms
- New data fetched from backend
- UI updates instantly
- No page refresh needed

**Data Flow:**
```
Webcam → Detection → API → Frontend (every 1s)
                     ↓
                 Database
                     ↓
              Seat Map Update
```

---

## Visual Design Elements

### Color Coding

| Color | Meaning | Usage |
|-------|---------|-------|
| 🟢 Green | Available | Free seats |
| 🔴 Red | Occupied | Seats in use |
| 🟠 Orange | Alert | Time exceeded |
| 🔵 Blue | Info | People count |
| ⚪ Gray | Inactive | Camera stopped |

### Animations

1. **Pulse Effect**: Time exceeded seats
2. **Fade In**: Page transitions
3. **Hover Effects**: Interactive elements
4. **Loading Spinners**: During API calls
5. **Slide Notifications**: Success/error messages

---

## Mobile Responsive Design

The app works perfectly on all devices:

### Desktop (1400px+)
- Side-by-side video and stats
- Large seat grid (6+ columns)
- Full analytics dashboard

### Tablet (768px - 1024px)
- Stacked video and stats
- Medium seat grid (4 columns)
- Collapsed navigation

### Mobile (<768px)
- Single column layout
- Compact seat grid (3 columns)
- Touch-friendly buttons
- Hamburger menu

---

## Notifications

The app shows real-time notifications for:

✅ **Success** (Green)
- Camera started
- Camera stopped

❌ **Error** (Red)
- Failed to start camera
- Connection lost

ℹ️ **Info** (Blue)
- Status changes
- Updates

Notifications appear in the top-right corner and auto-dismiss after 3 seconds.

---

## Activity Log

The activity feed shows recent events:

```
12:34 PM - Camera started successfully
12:35 PM - Seat occupied (5 total)
12:36 PM - Seat freed (8 available)
12:37 PM - Time limit exceeded for Seat 3
```

- Shows last 10 activities
- Newest at top
- Timestamp for each event
- Auto-scrolls

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1` | Go to Webcam Control |
| `2` | Go to Seat Map |
| `3` | Go to Analytics |
| `S` | Start Camera |
| `T` | Stop Camera |
| `R` | Refresh Data |

---

## Configuration

### Adjust Update Interval

Edit `static/js/app.js` line 187:

```javascript
// Default: 1000ms (1 second)
AppState.updateInterval = setInterval(updateOccupancyData, 1000);

// Change to 500ms for faster updates
AppState.updateInterval = setInterval(updateOccupancyData, 500);

// Change to 2000ms for slower updates
AppState.updateInterval = setInterval(updateOccupancyData, 2000);
```

### Customize Seat Grid Layout

Edit `static/css/styles.css` line 530:

```css
/* Default: auto-fit with 80px minimum */
.seat-grid {
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
}

/* Fixed 6 columns */
.seat-grid {
    grid-template-columns: repeat(6, 1fr);
}

/* Larger seats */
.seat-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
}
```

### Change Colors

Edit `static/css/styles.css` lines 10-20:

```css
:root {
    --primary: #667eea;     /* Main color */
    --success: #48bb78;     /* Green (available) */
    --danger: #f56565;      /* Red (occupied) */
    --warning: #ed8936;     /* Orange (exceeded) */
}
```

---

## Integration Examples

### Get Seat Data Programmatically

```javascript
// JavaScript
fetch('http://localhost:8000/api/webcam/occupancy')
    .then(res => res.json())
    .then(data => {
        console.log(`Available seats: ${data.data.available_seats}`);
        console.log('Seat details:', data.data.seats);
    });
```

### Python Integration

```python
import requests

response = requests.get('http://localhost:8000/api/webcam/occupancy')
data = response.json()

if data['status'] == 'running':
    print(f"Available: {data['data']['available_seats']}")
    for seat in data['data']['seats']:
        print(f"Seat {seat['id']}: {'Occupied' if seat['occupied'] else 'Available'}")
```

### Display on External Screen

```html
<!-- Embed seat map on another page -->
<iframe
    src="http://localhost:8000#seatmap"
    width="100%"
    height="600px"
    frameborder="0">
</iframe>
```

---

## Troubleshooting

### Seats Not Updating

**Problem**: Seat map shows old data

**Solutions**:
1. Check if camera is running (green badge)
2. Hard refresh page (Ctrl+F5)
3. Check browser console for errors (F12)
4. Verify API is accessible: http://localhost:8000/api/webcam/status

### Video Stream Not Loading

**Problem**: Black screen or no video

**Solutions**:
1. Click "Stop" then "Start" camera
2. Try different camera index (1, 2)
3. Check camera permissions
4. Close other apps using camera
5. Restart the API server

### Slow Updates

**Problem**: UI feels laggy

**Solutions**:
1. Reduce update interval to 2000ms (see Configuration)
2. Use GPU: Set `MODEL_DEVICE=0` in .env
3. Increase confidence threshold
4. Close other browser tabs

### Seat Grid Not Displaying

**Problem**: Empty seat grid

**Solutions**:
1. Ensure camera is started
2. Point camera at seating area
3. Check that chairs are visible
4. Lower confidence threshold
5. Improve lighting

---

## Performance Tips

### For Best Performance

1. **Use Chrome or Firefox** for best compatibility
2. **Close unnecessary tabs** to free memory
3. **Use Ethernet** instead of WiFi if possible
4. **Enable GPU** in .env file
5. **Adjust update interval** based on needs

### Recommended Settings

```env
# .env file
MODEL_CONF_THRESHOLD=0.4
MODEL_DEVICE=0
OCCUPANCY_TIME_THRESHOLD=10
```

### Browser Requirements

- **Minimum**: Chrome 90+, Firefox 88+, Safari 14+
- **Recommended**: Latest Chrome or Firefox
- **JavaScript**: Must be enabled
- **Cookies**: Not required

---

## Advanced Features

### Auto-Start Camera on Page Load

Edit `static/js/app.js` at the end of `checkInitialStatus()`:

```javascript
// Add after line 476
if (!data.is_running) {
    // Auto-start camera
    setTimeout(() => startCamera(), 1000);
}
```

### Sound Alerts

Add to `static/js/app.js`:

```javascript
function playSeatAlert() {
    const audio = new Audio('/static/alert.mp3');
    audio.play();
}

// In updateOccupancyData() when time exceeded:
if (seat.time_exceeded) {
    playSeatAlert();
}
```

### Export Data to CSV

Add button to download seat data:

```javascript
function exportToCSV() {
    const seats = Object.values(AppState.seatData);
    const csv = seats.map(s =>
        `${s.id},${s.occupied},${s.duration}`
    ).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'seat-data.csv';
    a.click();
}
```

---

## Security Considerations

1. **Access Control**: Use firewall to restrict access
2. **HTTPS**: Enable in production
3. **API Keys**: Enable authentication
4. **CORS**: Limit allowed origins
5. **Privacy**: Inform users about monitoring

---

## Support & Help

### Quick Links
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Webcam Status**: http://localhost:8000/api/webcam/status

### Browser Console
Press F12 to open developer tools and check for errors

### Common Error Messages

| Error | Solution |
|-------|----------|
| "Failed to start camera" | Check camera permissions |
| "Connection refused" | Start the API server |
| "404 Not Found" | Verify server is running |
| "CORS error" | Enable CORS in .env |

---

## What's Different from Old Version

### Old Version (index.html):
- Single page
- Basic controls
- Simple statistics
- Static layout

### New Version (app.html):
- ✨ **3 pages** with navigation
- 🎭 **Visual seat map** (movie-style)
- ⚡ **1-second real-time updates**
- 📊 **Analytics dashboard**
- 📱 **Responsive design**
- 🎨 **Modern UI/UX**
- 🔔 **Activity feed**
- 💫 **Animations**

---

## Summary

You now have a **professional, multi-page web application** that provides:

1. **Webcam Control** - Full camera management
2. **Visual Seat Map** - Real-time seat grid (like movie booking)
3. **Analytics** - Detailed statistics and insights
4. **Real-time Updates** - 1-second refresh intervals
5. **Beautiful UI** - Modern, responsive design
6. **Activity Tracking** - Event logging

Perfect for libraries, offices, study halls, restaurants, and any space with seating!

---

**Access the app at: http://localhost:8000**

**Enjoy your professional seat monitoring system! 🎉**
