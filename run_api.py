#!/usr/bin/env python3
"""
Quick start script for running the API server
"""
import os
import sys
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'torch',
        'cv2'
    ]

    missing = []
    for package in required_packages:
        try:
            if package == 'cv2':
                __import__('cv2')
            else:
                __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print("❌ Missing required packages:")
        for pkg in missing:
            pkg_name = 'opencv-python' if pkg == 'cv2' else pkg
            print(f"   - {pkg_name}")
        print("\nInstall with:")
        print("   pip install -r requirements.txt")
        print("   pip install -r requirements-api.txt")
        return False

    return True

def check_model_weights():
    """Check if model weights exist"""
    weights_path = Path("yolov7.pt")
    if not weights_path.exists():
        print("⚠️  Model weights not found: yolov7.pt")
        print("Download with: python download_models.py")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    else:
        print("✓ Model weights found")

    return True

def check_env_file():
    """Check if .env file exists"""
    env_path = Path(".env")
    if not env_path.exists():
        print("⚠️  .env file not found")
        print("Copying .env.example to .env...")
        example_path = Path(".env.example")
        if example_path.exists():
            import shutil
            shutil.copy(example_path, env_path)
            print("✓ Created .env file")
        else:
            print("❌ .env.example not found")
            return False
    else:
        print("✓ .env file found")

    return True

def create_directories():
    """Create required directories"""
    directories = ['uploads', 'outputs', 'jobs', 'api/logs']
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print("✓ Created required directories")

def main():
    """Main entry point"""
    print("=" * 60)
    print("Library Seat Occupancy Detection API")
    print("=" * 60)
    print()

    # Checks
    print("Running pre-flight checks...\n")

    if not check_requirements():
        sys.exit(1)
    print("✓ All required packages installed")

    if not check_env_file():
        sys.exit(1)

    if not check_model_weights():
        sys.exit(1)

    create_directories()

    print()
    print("=" * 60)
    print("Starting API server...")
    print("=" * 60)
    print()
    print("📍 Server will be available at: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()

    # Import and run uvicorn
    try:
        import uvicorn
        from api.config import settings

        uvicorn.run(
            "api.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.api_reload,
            log_level=settings.log_level.lower()
        )
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
