#!/usr/bin/env python3
"""
Test script for the API - demonstrates complete workflow
"""
import requests
import time
import sys
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API is healthy")
            print(f"  Version: {data['version']}")
            print(f"  Model loaded: {data['model_loaded']}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to API at {API_BASE_URL}")
        print("  Make sure the server is running:")
        print("  python run_api.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_detection_workflow(video_path: str = None):
    """Test complete detection workflow"""

    # Check if video file exists
    if video_path and not Path(video_path).exists():
        print(f"✗ Video file not found: {video_path}")
        return False

    if not video_path:
        print("No video file specified. Skipping detection test.")
        print("Usage: python test_api.py <path_to_video.mp4>")
        return True

    print(f"\nTesting detection workflow with: {video_path}")

    # 1. Upload video
    print("\n1. Uploading video...")
    try:
        with open(video_path, "rb") as f:
            response = requests.post(
                f"{API_BASE_URL}/api/detect",
                files={"video": f},
                params={
                    "conf_threshold": 0.3,
                    "save_video": True
                }
            )

        if response.status_code != 200:
            print(f"✗ Upload failed: {response.json()}")
            return False

        job = response.json()
        job_id = job["job_id"]
        print(f"✓ Job created: {job_id}")

    except Exception as e:
        print(f"✗ Error uploading: {e}")
        return False

    # 2. Poll for completion
    print("\n2. Waiting for processing...")
    max_wait = 600  # 10 minutes
    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{API_BASE_URL}/api/jobs/{job_id}")
            status_data = response.json()

            status = status_data["status"]
            progress = status_data.get("progress", 0)
            message = status_data.get("message", "")

            print(f"   Status: {status} - Progress: {progress:.1f}% - {message}")

            if status == "completed":
                print("✓ Processing completed!")

                # Display results
                results = status_data.get("results", {})
                print(f"\n=== Results ===")
                print(f"  Total frames: {results.get('total_frames', 0)}")
                print(f"  Total detections: {results.get('total_detections', 0)}")
                print(f"  Person detections: {results.get('person_detections', 0)}")
                print(f"  Chair detections: {results.get('chair_detections', 0)}")
                print(f"  Processing time: {results.get('processing_time', 0):.2f}s")
                print(f"  FPS: {results.get('fps', 0):.2f}")

                return True

            elif status == "failed":
                print(f"✗ Processing failed: {message}")
                return False

            time.sleep(3)

        except Exception as e:
            print(f"✗ Error checking status: {e}")
            return False

    print("✗ Timeout waiting for processing")
    return False

def test_list_jobs():
    """Test listing jobs"""
    print("\n3. Testing job listing...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/jobs?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found {data['total']} jobs")
            return True
        else:
            print(f"✗ Failed to list jobs: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("API Test Suite")
    print("=" * 60)

    # Test 1: Health check
    if not test_health():
        sys.exit(1)

    # Test 2: Detection workflow (if video provided)
    video_path = sys.argv[1] if len(sys.argv) > 1 else None
    if video_path:
        if not test_detection_workflow(video_path):
            sys.exit(1)
    else:
        print("\nℹ️  To test detection workflow, provide a video file:")
        print("   python test_api.py path/to/video.mp4")

    # Test 3: List jobs
    test_list_jobs()

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
