/**
 * Live Seat Map - Fetches real-time data from database
 * Students can view this without needing camera access
 */

let refreshInterval = null;
let isRefreshing = false;

// Start auto-refresh when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Seat Map Live View loaded');

    // Initial fetch
    fetchSeatsFromDatabase();

    // Auto-refresh every 2 seconds
    startAutoRefresh(2000);
});

function startAutoRefresh(intervalMs = 2000) {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }

    refreshInterval = setInterval(() => {
        fetchSeatsFromDatabase();
    }, intervalMs);

    console.log(`Auto-refresh started: every ${intervalMs}ms`);
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
        console.log('Auto-refresh stopped');
    }
}

async function fetchSeatsFromDatabase() {
    if (isRefreshing) return; // Prevent concurrent requests

    isRefreshing = true;

    try {
        const response = await fetch('/api/process/seats');

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            // Update seat map with database data
            updateSeatMapFromDatabase(data);
            updateLastRefreshTime();
        }

    } catch (error) {
        console.error('Error fetching seats:', error);
        showErrorState('Unable to fetch seat data. Is the server running?');
    } finally {
        isRefreshing = false;
    }
}

function updateSeatMapFromDatabase(data) {
    const seatGrid = document.getElementById('seatGrid');
    const mapTotalSeats = document.getElementById('mapTotalSeats');
    const mapAvailableSeats = document.getElementById('mapAvailableSeats');
    const mapOccupiedSeats = document.getElementById('mapOccupiedSeats');

    if (!seatGrid) return;

    // Update stats counters
    if (mapTotalSeats) mapTotalSeats.textContent = data.total_seats || 0;
    if (mapAvailableSeats) mapAvailableSeats.textContent = data.available_seats || 0;
    if (mapOccupiedSeats) mapOccupiedSeats.textContent = data.occupied_seats || 0;

    const seats = data.seats || [];

    console.log(`Rendering ${seats.length} seats from database`);

    if (seats.length === 0) {
        seatGrid.innerHTML = `
            <div class="empty-state">
                <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                </svg>
                <p>No seat data available</p>
                <p class="text-muted">Library camera may not be active</p>
                <button class="btn btn-primary" onclick="fetchSeatsFromDatabase()">Refresh</button>
            </div>
        `;
        return;
    }

    // Create seat grid
    let gridHTML = '';
    seats.forEach((seat) => {
        // Determine seat class based on status
        let seatClass = 'seat-available';
        if (seat.status === 'occupied') {
            seatClass = seat.duration_exceeded ? 'seat-exceeded' : 'seat-occupied';
        }

        // Calculate duration in minutes
        const durationMinutes = seat.duration ? Math.floor(seat.duration / 60) : 0;
        const durationText = seat.status === 'occupied' ? `${durationMinutes}m` : '';

        // Format occupied since time
        let occupiedSince = '';
        if (seat.occupied_since) {
            const sinceDate = new Date(seat.occupied_since);
            occupiedSince = sinceDate.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit'
            });
        }

        gridHTML += `
            <div class="seat-item ${seatClass}"
                 title="Seat ${seat.id} - ${seat.status}${occupiedSince ? ' since ' + occupiedSince : ''}"
                 data-seat-id="${seat.id}">
                <div class="seat-icon">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        ${seat.status === 'occupied'
                            ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>'
                            : '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>'
                        }
                    </svg>
                </div>
                <div class="seat-label">S${seat.id}</div>
                ${durationText ? `<div class="seat-duration">${durationText}</div>` : ''}
                ${seat.duration_exceeded ? '<div class="seat-alert">⚠️</div>' : ''}
            </div>
        `;
    });

    seatGrid.innerHTML = gridHTML;

    // Add pulse animation to newly occupied seats
    addSeatAnimations();
}

function addSeatAnimations() {
    const occupiedSeats = document.querySelectorAll('.seat-occupied, .seat-exceeded');
    occupiedSeats.forEach(seat => {
        seat.style.animation = 'none';
        setTimeout(() => {
            seat.style.animation = '';
        }, 10);
    });
}

function updateLastRefreshTime() {
    const refreshIndicator = document.getElementById('lastRefresh');
    if (refreshIndicator) {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        refreshIndicator.textContent = `Last updated: ${timeString}`;
    }
}

function showErrorState(message) {
    const seatGrid = document.getElementById('seatGrid');
    if (seatGrid) {
        seatGrid.innerHTML = `
            <div class="empty-state">
                <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <p class="text-danger">${message}</p>
                <button class="btn btn-primary" onclick="fetchSeatsFromDatabase()">Retry</button>
            </div>
        `;
    }
}

// Export functions for use in main app
window.fetchSeatsFromDatabase = fetchSeatsFromDatabase;
window.startAutoRefresh = startAutoRefresh;
window.stopAutoRefresh = stopAutoRefresh;
