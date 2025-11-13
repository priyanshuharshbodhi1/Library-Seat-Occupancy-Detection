// Global State
const AppState = {
    API_BASE: window.location.origin,
    isRunning: false,
    updateInterval: null,
    currentPage: 'webcam',
    seatData: {},
    activityLog: [],
    stats: {
        totalSeats: 0,
        occupiedSeats: 0,
        availableSeats: 0,
        personCount: 0
    }
};

// Initialize App
document.addEventListener('DOMContentLoaded', function() {
    console.log('App initializing...');
    setupNavigation();
    checkInitialStatus();
    navigateToPage('webcam');
});

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
        updateSeatMap();
    } else if (pageName === 'analytics') {
        updateAnalytics();
    }
}

// Webcam Control Functions
async function startCamera() {
    const cameraIndex = document.getElementById('cameraSelect').value;
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');

    startBtn.disabled = true;
    startBtn.innerHTML = '<span class="btn-icon">⏳</span> Starting...';

    try {
        const response = await fetch(`${AppState.API_BASE}/api/webcam/start?camera_index=${cameraIndex}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            AppState.isRunning = true;

            // Update video stream
            const videoStream = document.getElementById('videoStream');
            videoStream.src = `${AppState.API_BASE}/api/webcam/stream?t=${Date.now()}`;
            videoStream.style.display = 'block';
            document.getElementById('videoPlaceholder').style.display = 'none';

            // Update buttons
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
            startRealTimeUpdates();
            addActivity('Camera started successfully');
            showNotification('Camera started successfully!', 'success');

        } else {
            throw new Error(data.detail || 'Failed to start camera');
        }
    } catch (error) {
        console.error('Error starting camera:', error);
        startBtn.disabled = false;
        startBtn.innerHTML = `
            <svg class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            Start Camera
        `;
        showNotification('Failed to start camera: ' + error.message, 'error');
    }
}

async function stopCamera() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');

    stopBtn.disabled = true;
    stopBtn.innerHTML = '<span class="btn-icon">⏳</span> Stopping...';

    try {
        const response = await fetch(`${AppState.API_BASE}/api/webcam/stop`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            AppState.isRunning = false;

            // Update video stream
            document.getElementById('videoStream').style.display = 'none';
            document.getElementById('videoPlaceholder').style.display = 'flex';
            document.getElementById('videoStream').src = '';

            // Update buttons
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
            stopRealTimeUpdates();
            resetStats();
            addActivity('Camera stopped');
            showNotification('Camera stopped successfully!', 'info');

        } else {
            throw new Error(data.detail || 'Failed to stop camera');
        }
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

// Status Updates
function updateStatus(status) {
    const indicator = document.getElementById('statusIndicator');
    if (status === 'running') {
        indicator.className = 'status-badge status-running';
        indicator.innerHTML = '<span class="status-dot"></span> Camera Running';
    } else {
        indicator.className = 'status-badge status-stopped';
        indicator.innerHTML = '<span class="status-dot"></span> Camera Stopped';
    }
}

// Real-Time Updates (Every 1 Second)
function startRealTimeUpdates() {
    updateOccupancyData(); // Initial update
    AppState.updateInterval = setInterval(updateOccupancyData, 1000); // Update every 1 second
}

function stopRealTimeUpdates() {
    if (AppState.updateInterval) {
        clearInterval(AppState.updateInterval);
        AppState.updateInterval = null;
    }
}

async function updateOccupancyData() {
    if (!AppState.isRunning) return;

    try {
        const response = await fetch(`${AppState.API_BASE}/api/webcam/occupancy`);
        const result = await response.json();

        if (result.status === 'running' && result.data) {
            const data = result.data;

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
                AppState.seatData = {};
                data.seats.forEach(seat => {
                    AppState.seatData[seat.id] = seat;
                });

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
                    updateSeatMap();
                }

                // Update analytics if on that page
                if (AppState.currentPage === 'analytics') {
                    updateAnalytics();
                }
            }
        }
    } catch (error) {
        console.error('Error updating occupancy:', error);
    }
}

function updateStatsDisplay() {
    // Update webcam page stats
    document.getElementById('totalSeats').textContent = AppState.stats.totalSeats;
    document.getElementById('availableSeats').textContent = AppState.stats.availableSeats;
    document.getElementById('occupiedSeats').textContent = AppState.stats.occupiedSeats;
    document.getElementById('personCount').textContent = AppState.stats.personCount;

    // Update seat map stats
    document.getElementById('mapTotalSeats').textContent = AppState.stats.totalSeats;
    document.getElementById('mapAvailableSeats').textContent = AppState.stats.availableSeats;
    document.getElementById('mapOccupiedSeats').textContent = AppState.stats.occupiedSeats;
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

// Seat Map Visualization (Like Movie Booking)
function updateSeatMap() {
    const seatGrid = document.getElementById('seatGrid');

    if (Object.keys(AppState.seatData).length === 0) {
        seatGrid.innerHTML = `
            <div class="empty-state">
                <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                </svg>
                <p>Start the webcam to detect and display seats</p>
                <button class="btn btn-primary" onclick="navigateToPage('webcam')">Go to Webcam Control</button>
            </div>
        `;
        return;
    }

    // Create seat grid
    seatGrid.innerHTML = '';
    const seats = Object.values(AppState.seatData).sort((a, b) => a.id - b.id);

    seats.forEach(seat => {
        const seatElement = document.createElement('div');
        seatElement.className = `seat seat-icon`;

        let statusClass = 'seat-available';
        let statusText = 'Free';
        let durationText = '';

        if (seat.occupied) {
            if (seat.time_exceeded) {
                statusClass = 'seat-exceeded';
                statusText = 'Exceeded';
            } else {
                statusClass = 'seat-occupied';
                statusText = 'Busy';
            }
            const minutes = Math.floor(seat.duration / 60);
            const seconds = Math.floor(seat.duration % 60);
            durationText = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }

        seatElement.classList.add(statusClass);
        seatElement.innerHTML = `
            <div class="seat-number">${seat.id}</div>
            <div class="seat-status-text">${statusText}</div>
            ${durationText ? `<div class="seat-duration">${durationText}</div>` : ''}
        `;

        // Add tooltip on hover
        seatElement.title = `Seat ${seat.id} - ${seat.occupied ? 'Occupied' : 'Available'}${durationText ? ' (' + durationText + ')' : ''}`;

        seatGrid.appendChild(seatElement);
    });
}

// Analytics Page
function updateAnalytics() {
    // Calculate occupancy percentage
    const occupancyPercent = AppState.stats.totalSeats > 0
        ? (AppState.stats.occupiedSeats / AppState.stats.totalSeats * 100).toFixed(1)
        : 0;

    document.getElementById('occupancyBar').style.width = `${occupancyPercent}%`;
    document.getElementById('occupancyPercent').textContent = `${occupancyPercent}%`;

    // Calculate average duration
    const seats = Object.values(AppState.seatData);
    const occupiedSeats = seats.filter(s => s.occupied);
    const avgDuration = occupiedSeats.length > 0
        ? occupiedSeats.reduce((sum, s) => sum + s.duration, 0) / occupiedSeats.length
        : 0;

    const avgMinutes = Math.floor(avgDuration / 60);
    const avgSeconds = Math.floor(avgDuration % 60);
    document.getElementById('avgDuration').textContent = `${avgMinutes}:${avgSeconds.toString().padStart(2, '0')}`;

    // Peak usage (for now, just show current time if high occupancy)
    const peakTime = occupancyPercent > 50 ? new Date().toLocaleTimeString() : '--:--';
    document.getElementById('peakUsage').textContent = peakTime;

    // Update seat details
    const seatDetailsList = document.getElementById('seatDetails');
    if (seats.length === 0) {
        seatDetailsList.innerHTML = `
            <div class="empty-state-small">
                <p>No seat data available</p>
            </div>
        `;
        return;
    }

    seatDetailsList.innerHTML = seats.map(seat => {
        const statusClass = seat.time_exceeded ? 'exceeded' : (seat.occupied ? 'occupied' : '');
        const statusText = seat.occupied ? 'Occupied' : 'Available';
        const duration = seat.occupied ? Math.floor(seat.duration) : 0;
        const exceededWarning = seat.time_exceeded ? '<br><span style="color: #ed8936;">⚠️ TIME EXCEEDED</span>' : '';

        return `
            <div class="seat-detail-item ${statusClass}">
                <div class="seat-detail-info">
                    <h4>Seat ${seat.id}</h4>
                    <p>${statusText}${seat.occupied ? ` for ${duration}s` : ''}${exceededWarning}</p>
                </div>
                <div class="seat-detail-status">
                    <span class="status-dot ${seat.occupied ? 'occupied' : 'available'}"></span>
                    <span>${statusText}</span>
                </div>
            </div>
        `;
    }).join('');
}

// Activity Log
function addActivity(message) {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

    AppState.activityLog.unshift({
        time: timeString,
        message: message
    });

    // Keep only last 10 activities
    if (AppState.activityLog.length > 10) {
        AppState.activityLog.pop();
    }

    updateActivityLog();
}

function updateActivityLog() {
    const activityList = document.getElementById('activityLog');

    if (AppState.activityLog.length === 0) {
        activityList.innerHTML = `
            <div class="activity-item">
                <span class="activity-time">--:--</span>
                <span class="activity-text">No recent activity</span>
            </div>
        `;
        return;
    }

    activityList.innerHTML = AppState.activityLog.map(activity => `
        <div class="activity-item">
            <span class="activity-time">${activity.time}</span>
            <span class="activity-text">${activity.message}</span>
        </div>
    `).join('');
}

// Check Initial Status
async function checkInitialStatus() {
    try {
        const response = await fetch(`${AppState.API_BASE}/api/webcam/status`);
        const data = await response.json();

        if (data.is_running) {
            AppState.isRunning = true;

            // Update video stream
            const videoStream = document.getElementById('videoStream');
            videoStream.src = `${AppState.API_BASE}/api/webcam/stream?t=${Date.now()}`;
            videoStream.style.display = 'block';
            document.getElementById('videoPlaceholder').style.display = 'none';

            // Update buttons
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;

            updateStatus('running');
            startRealTimeUpdates();
            addActivity('Camera was already running');
        }
    } catch (error) {
        console.error('Error checking initial status:', error);
    }
}

// Notifications
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: ${type === 'success' ? '#48bb78' : type === 'error' ? '#f56565' : '#4299e1'};
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;

    // Add animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(400px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(400px); opacity: 0; }
        }
    `;
    document.head.appendChild(style);

    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Export functions to global scope
window.startCamera = startCamera;
window.stopCamera = stopCamera;
window.navigateToPage = navigateToPage;

console.log('App initialized successfully');
