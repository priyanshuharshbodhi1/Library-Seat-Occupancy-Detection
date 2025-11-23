// Browser-based webcam capture with backend frame processing
// Video is captured in browser, frames sent to backend for detection

const AppState = {
    API_BASE: window.location.origin,
    isRunning: false,
    videoStream: null,
    videoElement: null,
    canvasElement: null,
    canvasContext: null,
    processInterval: null,
    currentPage: 'webcam',
    seatData: {},
    activityLog: [],
    stats: {
        totalSeats: 0,
        occupiedSeats: 0,
        availableSeats: 0,
        personCount: 0
    },
    processingFrame: false
};

// Initialize App
document.addEventListener('DOMContentLoaded', function() {
    console.log('App initializing...');
    setupNavigation();
    setupCanvas();
    navigateToPage('webcam');
});

// Setup Canvas for frame capture
function setupCanvas() {
    AppState.canvasElement = document.createElement('canvas');
    AppState.canvasContext = AppState.canvasElement.getContext('2d');
}

// Navigation System
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.dataset.page;
            navigateToPage(page);
        });
    });
}

function navigateToPage(pageName) {
    console.log('Navigating to page:', pageName);

    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.dataset.page === pageName) {
            link.classList.add('active');
        }
    });

    // Update active page
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(`${pageName}-page`).classList.add('active');

    AppState.currentPage = pageName;

    // Refresh data for the page
    if (pageName === 'seatmap') {
        console.log('Current seat data:', AppState.seatData);
        console.log('Number of seats:', Object.keys(AppState.seatData).length);

        // If camera is not running, fetch from database
        if (!AppState.isRunning) {
            console.log('Camera not running, fetching from database...');
            fetchAndUpdateSeatMap();
            // Start auto-refresh from database
            startDatabaseRefresh();
        } else {
            updateSeatMap();
        }
    } else {
        // Stop database refresh when leaving seat map
        stopDatabaseRefresh();
    }
}

// Database refresh for seat map
let databaseRefreshInterval = null;

function startDatabaseRefresh() {
    // Don't refresh from database if camera is running
    if (AppState.isRunning) return;

    stopDatabaseRefresh(); // Clear any existing interval

    // Refresh every 2 seconds
    databaseRefreshInterval = setInterval(() => {
        if (AppState.currentPage === 'seatmap' && !AppState.isRunning) {
            fetchAndUpdateSeatMap();
        } else {
            stopDatabaseRefresh();
        }
    }, 2000);

    console.log('Started database auto-refresh for seat map');
}

function stopDatabaseRefresh() {
    if (databaseRefreshInterval) {
        clearInterval(databaseRefreshInterval);
        databaseRefreshInterval = null;
        console.log('Stopped database auto-refresh');
    }
}

async function fetchAndUpdateSeatMap() {
    try {
        const response = await fetch(`${AppState.API_BASE}/api/process/seats`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            // Update stats
            AppState.stats = {
                totalSeats: data.total_seats || 0,
                occupiedSeats: data.occupied_seats || 0,
                availableSeats: data.available_seats || 0,
                personCount: 0
            };

            // Transform database seats to frontend format
            AppState.seatData = {};
            if (data.seats) {
                data.seats.forEach(seat => {
                    AppState.seatData[seat.id] = {
                        id: seat.id,
                        status: seat.status,
                        occupied: seat.status === 'occupied',
                        duration: seat.duration || 0,
                        duration_exceeded: seat.duration_exceeded || false,
                        time_exceeded: seat.duration_exceeded || false,
                        bbox: seat.bbox,
                        occupied_since: seat.occupied_since
                    };
                });
            }

            console.log(`Fetched ${data.seats?.length || 0} seats from database`);

            // Update the display
            updateStatsDisplay();
            updateSeatMap();
            updateDataSourceIndicator('database');
        }

    } catch (error) {
        console.error('Error fetching seats from database:', error);
        updateDataSourceIndicator('error');
    }
}

function updateDataSourceIndicator(source) {
    const indicator = document.getElementById('dataSourceText');
    const timeIndicator = document.getElementById('lastRefreshTime');

    if (!indicator) return;

    const now = new Date().toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    if (source === 'database') {
        indicator.innerHTML = 'Data Source: Database';
        indicator.style.color = '#48bb78'; // Green
        if (timeIndicator) {
            timeIndicator.textContent = `Updated: ${now}`;
        }
    } else if (source === 'live') {
        indicator.innerHTML = 'Data Source: Live Camera';
        indicator.style.color = '#4299e1'; // Blue
        if (timeIndicator) {
            timeIndicator.textContent = `Live`;
        }
    } else if (source === 'error') {
        indicator.innerHTML = 'Unable to fetch data';
        indicator.style.color = '#f56565'; // Red
        if (timeIndicator) {
            timeIndicator.textContent = `Error at ${now}`;
        }
    }
}

// Webcam Control - Browser Capture
async function startCamera() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');

    startBtn.disabled = true;
    startBtn.innerHTML = '<span class="btn-icon">⏳</span> Starting...';

    try {
        // Request camera permission from browser
        console.log('Requesting camera access...');

        const constraints = {
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            },
            audio: false
        };

        // Get user media (this triggers permission popup)
        AppState.videoStream = await navigator.mediaDevices.getUserMedia(constraints);

        console.log('Camera access granted!');

        // Create or get video element
        let videoElement = document.getElementById('localVideo');
        if (!videoElement) {
            videoElement = document.createElement('video');
            videoElement.id = 'localVideo';
            videoElement.autoplay = true;
            videoElement.playsInline = true;
            videoElement.muted = true;
            videoElement.style.width = '100%';
            videoElement.style.display = 'block';

            // Replace placeholder
            const videoContainer = document.querySelector('.video-container');
            videoContainer.innerHTML = '';
            videoContainer.appendChild(videoElement);
        }

        AppState.videoElement = videoElement;
        videoElement.srcObject = AppState.videoStream;

        // Wait for video to be ready
        await new Promise((resolve) => {
            videoElement.onloadedmetadata = () => {
                console.log('Video metadata loaded');
                resolve();
            };
        });

        await videoElement.play();
        console.log('Video playing');

        // Setup canvas for frame capture
        AppState.canvasElement.width = videoElement.videoWidth;
        AppState.canvasElement.height = videoElement.videoHeight;

        console.log(`Canvas size: ${AppState.canvasElement.width}x${AppState.canvasElement.height}`);

        AppState.isRunning = true;

        // Update UI
        startBtn.disabled = true;
        stopBtn.disabled = false;
        startBtn.innerHTML = `
            <svg class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            Start Camera
        `;

        updateStatus('running');
        startFrameProcessing();
        addActivity('Camera started successfully');
        showNotification('Camera started! Processing frames...', 'success');

    } catch (error) {
        console.error('Error starting camera:', error);

        let errorMessage = 'Failed to access camera: ';
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            errorMessage += 'Permission denied. Please allow camera access.';
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
            errorMessage += 'No camera found. Please connect a camera.';
        } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
            errorMessage += 'Camera is already in use by another application.';
        } else {
            errorMessage += error.message || 'Unknown error';
        }

        startBtn.disabled = false;
        startBtn.innerHTML = `
            <svg class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            Start Camera
        `;
        showNotification(errorMessage, 'error');
        addActivity(errorMessage);
    }
}

async function stopCamera() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');

    stopBtn.disabled = true;
    stopBtn.innerHTML = '<span class="btn-icon">⏳</span> Stopping...';

    try {
        // Stop video stream
        if (AppState.videoStream) {
            AppState.videoStream.getTracks().forEach(track => track.stop());
            AppState.videoStream = null;
        }

        // Stop video element
        if (AppState.videoElement) {
            AppState.videoElement.srcObject = null;
        }

        // Stop processing
        stopFrameProcessing();
        AppState.isRunning = false;

        // Update UI
        const videoContainer = document.querySelector('.video-container');
        videoContainer.innerHTML = `
            <div id="videoPlaceholder" class="video-placeholder">
                <svg class="placeholder-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                </svg>
                <p>Click "Start Camera" to begin monitoring</p>
            </div>
        `;

        startBtn.disabled = false;
        stopBtn.disabled = true;
        stopBtn.innerHTML = `
            <svg class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"></path>
            </svg>
            Stop Camera
        `;

        updateStatus('stopped');
        resetStats();
        addActivity('Camera stopped');
        showNotification('Camera stopped successfully!', 'info');

    } catch (error) {
        console.error('Error stopping camera:', error);
        stopBtn.disabled = false;
        stopBtn.innerHTML = `
            <svg class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"></path>
            </svg>
            Stop Camera
        `;
        showNotification('Failed to stop camera: ' + error.message, 'error');
    }
}

// Frame Processing - Send frames to backend
function startFrameProcessing() {
    console.log('Starting frame processing (1 frame per second)...');
    processFrame(); // Process first frame immediately
    AppState.processInterval = setInterval(processFrame, 1000); // Process every 1 second
}

function stopFrameProcessing() {
    if (AppState.processInterval) {
        clearInterval(AppState.processInterval);
        AppState.processInterval = null;
    }
}

async function processFrame() {
    if (!AppState.isRunning || !AppState.videoElement || AppState.processingFrame) {
        return;
    }

    try {
        AppState.processingFrame = true;

        // Capture frame from video
        AppState.canvasContext.drawImage(
            AppState.videoElement,
            0, 0,
            AppState.canvasElement.width,
            AppState.canvasElement.height
        );

        // Convert to base64 JPEG
        const frameData = AppState.canvasElement.toDataURL('image/jpeg', 0.8);

        // Send to backend for processing
        const formData = new FormData();
        formData.append('frame_data', frameData);

        const response = await fetch(`${AppState.API_BASE}/api/process/frame`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            // Update stats with detection results
            updateStatsFromDetections(result);

            // Draw bounding boxes on video (overlay)
            drawDetections(result.detections);
        }

    } catch (error) {
        console.error('Error processing frame:', error);
        // Don't show notification for every error, just log it
    } finally {
        AppState.processingFrame = false;
    }
}

function updateStatsFromDetections(result) {
    const data = result.occupancy;

    console.log('Processing detection results:', data);

    // Store previous state
    const prevStats = { ...AppState.stats };

    // Update stats
    AppState.stats = {
        totalSeats: data.total_seats || 0,
        occupiedSeats: data.occupied_seats || 0,
        availableSeats: data.available_seats || 0,
        personCount: data.person_count || 0
    };

    // Update UI
    updateStatsDisplay();

    // Update seat data
    if (data.seats) {
        console.log('Received seats from backend:', data.seats.length);
        AppState.seatData = {};
        data.seats.forEach(seat => {
            // Transform backend format to frontend format
            AppState.seatData[seat.id] = {
                id: seat.id,
                status: seat.occupied ? 'occupied' : 'available',
                occupied: seat.occupied,
                duration: seat.duration || 0,
                duration_exceeded: seat.time_exceeded || false,
                time_exceeded: seat.time_exceeded || false,
                bbox: seat.bbox
            };
        });

        console.log('Stored seat data:', Object.keys(AppState.seatData).length, 'seats');

        // Check for changes and log activity
        if (prevStats.occupiedSeats !== AppState.stats.occupiedSeats) {
            if (AppState.stats.occupiedSeats > prevStats.occupiedSeats) {
                addActivity(`Seat occupied (${AppState.stats.occupiedSeats} total)`);
            } else if (AppState.stats.occupiedSeats < prevStats.occupiedSeats) {
                addActivity(`Seat freed (${AppState.stats.availableSeats} available)`);
            }
        }

        // Update seat map if on that page
        if (AppState.currentPage === 'seatmap') {
            console.log('Updating seat map with', Object.keys(AppState.seatData).length, 'seats');
            updateSeatMap();
            updateDataSourceIndicator('live');
        }
    } else {
        console.log('No seats data in response');
    }
}

function drawDetections(detections) {
    if (!AppState.videoElement || !detections) return;

    // Create overlay canvas if it doesn't exist
    let overlayCanvas = document.getElementById('detectionOverlay');
    if (!overlayCanvas) {
        overlayCanvas = document.createElement('canvas');
        overlayCanvas.id = 'detectionOverlay';
        overlayCanvas.style.position = 'absolute';
        overlayCanvas.style.top = '0';
        overlayCanvas.style.left = '0';
        overlayCanvas.style.width = '100%';
        overlayCanvas.style.height = '100%';
        overlayCanvas.style.pointerEvents = 'none';

        const videoContainer = document.querySelector('.video-container');
        if (videoContainer) {
            videoContainer.style.position = 'relative';
            videoContainer.appendChild(overlayCanvas);
        }
    }

    // Set canvas size to match video
    const videoRect = AppState.videoElement.getBoundingClientRect();
    overlayCanvas.width = AppState.videoElement.videoWidth;
    overlayCanvas.height = AppState.videoElement.videoHeight;

    const ctx = overlayCanvas.getContext('2d');
    ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

    // Draw bounding boxes
    detections.forEach(det => {
        const [x1, y1, x2, y2] = det.bbox;
        const color = det.class === 0 ? '#48bb78' : '#4299e1'; // Green for person, blue for chair

        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

        // Draw label
        const label = `${det.class_name} ${(det.confidence * 100).toFixed(0)}%`;
        ctx.font = '16px Arial';
        const textWidth = ctx.measureText(label).width;

        ctx.fillStyle = color;
        ctx.fillRect(x1, y1 - 25, textWidth + 10, 25);

        ctx.fillStyle = 'white';
        ctx.fillText(label, x1 + 5, y1 - 7);
    });
}

// Status Management
function updateStatus(status) {
    const statusIndicator = document.getElementById('statusIndicator');
    if (!statusIndicator) return;

    statusIndicator.className = 'status-badge';

    if (status === 'running') {
        statusIndicator.classList.add('status-running');
        statusIndicator.innerHTML = '<span class="status-dot"></span> Camera Running';
    } else if (status === 'stopped') {
        statusIndicator.classList.add('status-stopped');
        statusIndicator.innerHTML = '<span class="status-dot"></span> Camera Stopped';
    } else if (status === 'error') {
        statusIndicator.classList.add('status-error');
        statusIndicator.innerHTML = '<span class="status-dot"></span> Error';
    }
}

// Stats Display
function updateStatsDisplay() {
    document.getElementById('totalSeats').textContent = AppState.stats.totalSeats;
    document.getElementById('availableSeats').textContent = AppState.stats.availableSeats;
    document.getElementById('occupiedSeats').textContent = AppState.stats.occupiedSeats;
    document.getElementById('personCount').textContent = AppState.stats.personCount;
}

function resetStats() {
    AppState.stats = {
        totalSeats: 0,
        occupiedSeats: 0,
        availableSeats: 0,
        personCount: 0
    };
    AppState.seatData = {};
    updateStatsDisplay();
}

// Seat Map Visualization - Theater Style
function updateSeatMap() {
    const seatGrid = document.getElementById('seatGrid');
    const mapTotalSeats = document.getElementById('mapTotalSeats');
    const mapAvailableSeats = document.getElementById('mapAvailableSeats');
    const mapOccupiedSeats = document.getElementById('mapOccupiedSeats');

    if (!seatGrid) return;

    // Update stats
    if (mapTotalSeats) mapTotalSeats.textContent = AppState.stats.totalSeats;
    if (mapAvailableSeats) mapAvailableSeats.textContent = AppState.stats.availableSeats;
    if (mapOccupiedSeats) mapOccupiedSeats.textContent = AppState.stats.occupiedSeats;

    // Generate seat grid
    const seats = Object.values(AppState.seatData);

    if (seats.length === 0) {
        seatGrid.innerHTML = `
            <div class="empty-state">
                <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                </svg>
                <p>No seat data available</p>
                <p class="text-muted">Library camera may not be active</p>
                <button class="btn btn-primary" onclick="navigateToPage('webcam')">Go to Webcam Control</button>
            </div>
        `;
        return;
    }

    // Organize seats into rows (6 seats per row for theater layout)
    const seatsPerRow = 6;
    const rows = [];
    const sortedSeats = seats.sort((a, b) => a.id - b.id);

    for (let i = 0; i < sortedSeats.length; i += seatsPerRow) {
        rows.push(sortedSeats.slice(i, i + seatsPerRow));
    }

    // Create theater-style grid with screen indicator
    let gridHTML = `
        <div class="theater-screen">
            Library View / Screen
        </div>
    `;

    // Generate rows with labels
    rows.forEach((row, rowIndex) => {
        const rowLabel = String.fromCharCode(65 + rowIndex); // A, B, C, D...

        row.forEach((seat, seatIndex) => {
            const seatClass = seat.status === 'occupied'
                ? (seat.duration_exceeded ? 'seat-exceeded' : 'seat-occupied')
                : 'seat-available';

            const duration = seat.duration ? Math.floor(seat.duration / 60) : 0;
            const durationText = seat.status === 'occupied' ? `${duration}m` : '';

            // Add aisle space in the middle (after 3rd seat)
            if (seatIndex === 3 && row.length > 3) {
                gridHTML += `<div class="seat-aisle"></div>`;
            }

            // Seat icon based on status
            let seatIcon = '';
            if (seat.status === 'occupied') {
                seatIcon = `
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                    </svg>
                `;
            } else {
                seatIcon = `
                    <svg fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path d="M7 13c1.66 0 3-1.34 3-3S8.66 7 7 7s-3 1.34-3 3 1.34 3 3 3zm12-6h-8v7H3V7H1v7c0 1.1.9 2 2 2h1v3h2v-3h8v3h2v-3h1c1.1 0 2-.9 2-2V7z"></path>
                    </svg>
                `;
            }

            gridHTML += `
                <div class="seat-item ${seatClass}"
                     title="Row ${rowLabel} - Seat ${seatIndex + 1}\n${seat.status === 'occupied' ? 'Occupied' : 'Available'}"
                     data-seat-id="${seat.id}">
                    <div class="seat-icon">
                        ${seatIcon}
                    </div>
                    <div class="seat-label">${rowLabel}${seatIndex + 1}</div>
                    ${durationText ? `<div class="seat-duration">${durationText}</div>` : ''}
                </div>
            `;
        });
    });

    // Set grid columns dynamically
    const cols = Math.min(seatsPerRow + 1, 7); // +1 for aisle
    seatGrid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
    seatGrid.innerHTML = gridHTML;
}

// Activity Log
function addActivity(message) {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    AppState.activityLog.unshift({
        time: timeStr,
        message: message
    });

    // Keep only last 10 activities
    if (AppState.activityLog.length > 10) {
        AppState.activityLog = AppState.activityLog.slice(0, 10);
    }

    updateActivityLog();
}

function updateActivityLog() {
    const activityLogEl = document.getElementById('activityLog');
    if (!activityLogEl) return;

    if (AppState.activityLog.length === 0) {
        activityLogEl.innerHTML = `
            <div class="activity-item">
                <span class="activity-time">--:--</span>
                <span class="activity-text">Waiting for camera to start...</span>
            </div>
        `;
        return;
    }

    let logHTML = '';
    AppState.activityLog.forEach(activity => {
        logHTML += `
            <div class="activity-item">
                <span class="activity-time">${activity.time}</span>
                <span class="activity-text">${activity.message}</span>
            </div>
        `;
    });

    activityLogEl.innerHTML = logHTML;
}

// Notifications
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;

    const icons = {
        success: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width: 20px; height: 20px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
        error: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width: 20px; height: 20px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
        warning: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width: 20px; height: 20px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>',
        info: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width: 20px; height: 20px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
    };

    notification.innerHTML = `
        <span class="notification-icon">${icons[type] || icons.info}</span>
        <span class="notification-message">${message}</span>
    `;

    // Add to body
    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    // Remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

// Add notification styles if not already in CSS
if (!document.getElementById('notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
        .notification {
            position: fixed;
            top: 16px;
            right: 16px;
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 12px 16px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            gap: 8px;
            z-index: 10000;
            transform: translateX(400px);
            transition: transform 0.2s;
            max-width: 350px;
            font-size: 0.75rem;
        }
        .notification.show {
            transform: translateX(0);
        }
        .notification-icon {
            width: 16px;
            height: 16px;
            flex-shrink: 0;
        }
        .notification-message {
            font-size: 0.75rem;
            color: var(--text);
        }
        .notification-success { border-color: var(--success); }
        .notification-success .notification-icon svg { stroke: var(--success); }
        .notification-error { border-color: var(--danger); }
        .notification-error .notification-icon svg { stroke: var(--danger); }
        .notification-warning { border-color: var(--warning); }
        .notification-warning .notification-icon svg { stroke: var(--warning); }
        .notification-info { border-color: var(--accent); }
        .notification-info .notification-icon svg { stroke: var(--accent); }
    `;
    document.head.appendChild(style);
}
