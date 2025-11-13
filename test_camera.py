#!/usr/bin/env python3
"""
Quick camera test script
Run this to diagnose camera issues
"""
import cv2
import sys
import codecs

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def test_camera(index=0):
    """Test camera access"""
    print(f"\n{'='*60}")
    print(f"Testing Camera {index}")
    print(f"{'='*60}\n")

    # Test 1: Normal VideoCapture
    print(f"Test 1: Normal VideoCapture({index})...")
    cap = cv2.VideoCapture(index)
    if cap.isOpened():
        print("✅ Camera opened successfully with default backend")
        ret, frame = cap.read()
        if ret:
            print(f"✅ Successfully read frame: {frame.shape}")
            cap.release()
            return True
        else:
            print("❌ Camera opened but cannot read frames")
        cap.release()
    else:
        print("❌ Failed with default backend")

    # Test 2: DirectShow (Windows)
    if sys.platform == 'win32':
        print(f"\nTest 2: DirectShow backend...")
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            print("✅ Camera opened with DirectShow")
            ret, frame = cap.read()
            if ret:
                print(f"✅ Successfully read frame: {frame.shape}")
                cap.release()
                return True
            cap.release()
        else:
            print("❌ Failed with DirectShow")

        # Test 3: MSMF (Windows)
        print(f"\nTest 3: MSMF backend...")
        cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
        if cap.isOpened():
            print("✅ Camera opened with MSMF")
            ret, frame = cap.read()
            if ret:
                print(f"✅ Successfully read frame: {frame.shape}")
                cap.release()
                return True
            cap.release()
        else:
            print("❌ Failed with MSMF")

    return False

def main():
    print("\n" + "="*60)
    print("Camera Diagnostic Tool")
    print("="*60)
    print("\nChecking OpenCV installation...")
    print(f"OpenCV version: {cv2.__version__}")
    print("✅ OpenCV is installed")

    # Test cameras 0, 1, 2
    cameras_found = []
    for i in range(3):
        if test_camera(i):
            cameras_found.append(i)

    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")

    if cameras_found:
        print(f"\n✅ Found {len(cameras_found)} working camera(s): {cameras_found}")
        print(f"\n🎯 Use camera index {cameras_found[0]} in the web app")
    else:
        print("\n❌ No working cameras found!")
        print("\n📋 Troubleshooting steps:")
        print("   1. Check if camera is physically connected")
        print("   2. Close other applications using the camera (Zoom, Teams, Skype)")
        print("   3. Check Windows Settings > Privacy > Camera")
        print("   4. Enable camera access for Python/Desktop apps")
        print("   5. Try restarting your computer")
        print("   6. Check Device Manager for camera drivers")

    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
