#!/bin/bash

echo "========================================"
echo "Library Seat Occupancy Monitor"
echo "Real-Time Webcam Detection"
echo "========================================"
echo ""

echo "Starting API server..."
echo ""
echo "Dashboard will be available at:"
echo "  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
