# 🎯 Library Seat Detection - Complete Setup Guide

## 📋 Prerequisites
- Python 3.8+ installed
- ~3GB free disk space
- Internet connection for model downloads

## 🚀 Setup Instructions

### 1. Navigate to project
```bash
cd /home/priyanshu/repos/Library-Seat-Occupancy-Detection
```

### 2. Create and activate virtual environment
```bash
# Create virtual environment (one-time setup)
python3 -m venv venv

# Activate virtual environment (do this every time)
source venv/bin/activate
```

### 3. Install dependencies
```bash
# Install all required packages (~3GB download)
pip install -r requirements.txt
```
**⏳ This takes 10-15 minutes depending on internet speed**

### 4. Verify installation
```bash
# Check if key packages are installed
python -c "import cv2, torch, numpy; print('✅ All packages installed successfully!')"
```

### 5. Run detection on your video
```bash
# Basic usage
python detect_and_track.py --source "library-demo-video.mp4"

# Advanced usage with custom settings
python detect_and_track.py \
    --weights yolov7.pt \
    --source "library-demo-video.mp4" \
    --conf-thres 0.4 \
    --classes 0 56 \
    --name "Library_Seat_Detection_Test"
```

### 6. Find your results
```bash
# Output video will be saved to:
ls runs/detect/*/
```

## 🔧 Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--source` | Input video file | Required |
| `--weights` | Model weights file | `yolov7.pt` |
| `--conf-thres` | Confidence threshold | 0.25 |
| `--classes` | Detect specific classes | All classes |
| `--name` | Output folder name | `object_tracking` |
| `--view-img` | Display real-time preview | False |

## 📊 Detected Classes
- **Class 0**: Person (human detection)
- **Class 56**: Chair (furniture detection)
- Use `--classes 0 56` to detect only people and chairs

## 🎯 Expected Output
- **Input**: `library-demo-video.mp4`
- **Output**: `runs/detect/{experiment_name}/library-demo-video.mp4`
- **Features**: 
  - Red boxes around people with tracking IDs
  - Yellow boxes around chairs
  - Occupancy time tracking
  - "TIME EXCEEDED" alerts for seats held too long

## 🛠️ Troubleshooting

### ModuleNotFoundError: No module named 'cv2'
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Verify installation completed
pip list | grep opencv
```

### Model weights not found
```bash
# First run will auto-download yolov7.pt (~74MB)
# Or download manually:
wget https://github.com/WongKinYiu/yolov7/releases/download/v0.1/yolov7.pt
```

### Virtual environment issues
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📁 Project Structure
```
Library-Seat-Occupancy-Detection/
├── detect_and_track.py     # Main detection script
├── sort.py                 # Object tracking algorithm  
├── models/                 # YOLOv7 architecture
├── utils/                  # Helper functions
├── data/                   # Configuration files
├── requirements.txt        # Python dependencies
├── venv/                   # Virtual environment (created)
├── library-demo-video.mp4  # Your test video
└── runs/detect/            # Output videos (created)
```

## 🔄 Daily Workflow
```bash
# 1. Navigate and activate
cd /home/priyanshu/repos/Library-Seat-Occupancy-Detection
source venv/bin/activate

# 2. Run detection
python detect_and_track.py --source "your_video.mp4"

# 3. Check results
ls runs/detect/*/

# 4. Deactivate when done
deactivate
```

## 💾 Disk Space Usage
- **Project files**: ~7MB
- **Virtual environment**: ~2.2GB  
- **YOLOv7 weights**: ~74MB
- **Total**: ~2.3GB

## ⚡ Performance Tips
- Use `--conf-thres 0.4` for better accuracy
- Add `--view-img` to see real-time detection
- Use smaller videos for testing (under 1GB)
- Close other applications for better performance
deactivate