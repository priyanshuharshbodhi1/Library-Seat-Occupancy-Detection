# 🚀 Quick Start Guide

Get SeatWatch running in 5 minutes! Follow these steps to detect seat occupancy in your library videos.

## ⚡ Fast Setup (5 minutes)

```bash
# 1. Clone and enter directory
git clone https://github.com/yourusername/Library-Seat-Occupancy-Detection
cd Library-Seat-Occupancy-Detection

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies (~2-3 minutes)
pip install -r requirements.txt

# 4. Download models (~1 minute)
python download_models.py

# 5. Test with your video
python detect_and_track.py --source your_video.mp4
```

## 📱 What You'll See

After running, check your results in:
```
runs/detect/exp/your_video.mp4
```

The output video will show:
- 🔴 **Red boxes** around people with ID numbers  
- 🟡 **Yellow boxes** around chairs
- ⏱️ **Timer** showing how long seats are occupied
- ⚠️ **"TIME EXCEEDED"** alerts for seats held too long

## 🎯 Best Results Tips

```bash
# For better accuracy (recommended)
python detect_and_track.py --source video.mp4 --conf-thres 0.4 --classes 0 56

# To see live preview while processing
python detect_and_track.py --source video.mp4 --view-img

# For custom output name
python detect_and_track.py --source video.mp4 --name "library_monday"
```

## ❗ Common Issues

**Can't find python3?** Try `python` instead of `python3`

**Installation taking forever?** 
- Check your internet connection
- Try: `pip install --upgrade pip` first

**"No module named cv2"?**
```bash
source venv/bin/activate  # Make sure venv is active
pip install opencv-python
```

**Need help?** See the full [README.md](README.md) for detailed troubleshooting.

---
**🎉 Ready to go!** Your library seat detection system is now running!
