#!/usr/bin/env python3
"""
Model Download Script for Library Seat Occupancy Detection
Downloads required model files that are too large for git repository
"""

import os
import sys
import urllib.request
from pathlib import Path

def download_file(url, filepath, description="file"):
    """Download file with progress bar"""
    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, (downloaded * 100) // total_size)
            bar_length = 50
            filled_length = int(bar_length * percent // 100)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            print(f'\rDownloading {description}: |{bar}| {percent}% ({downloaded//(1024*1024)}MB/{total_size//(1024*1024)}MB)', end='', flush=True)
    
    print(f"\n📥 Starting download: {description}")
    try:
        urllib.request.urlretrieve(url, filepath, progress_hook)
        print(f"\n✅ Successfully downloaded: {filepath}")
        return True
    except Exception as e:
        print(f"\n❌ Failed to download {description}: {e}")
        return False

def main():
    print("🚀 Library Seat Occupancy Detection - Model Downloader")
    print("=" * 60)
    
    # Define model files to download
    models = {
        "yolov7.pt": {
            "url": "https://github.com/WongKinYiu/yolov7/releases/download/v0.1/yolov7.pt",
            "size": "74 MB",
            "description": "YOLOv7 base model weights"
        }
    }
    
    # Check if models already exist
    existing_models = []
    missing_models = []
    
    for model_name, model_info in models.items():
        if os.path.exists(model_name):
            existing_models.append(model_name)
            print(f"✅ {model_name} already exists ({model_info['size']})")
        else:
            missing_models.append((model_name, model_info))
    
    if not missing_models:
        print("\n🎉 All model files are already downloaded!")
        return
    
    print(f"\n📋 Need to download {len(missing_models)} model file(s):")
    total_size = 0
    for model_name, model_info in missing_models:
        print(f"   • {model_name} ({model_info['size']}) - {model_info['description']}")
        # Rough size calculation for display
        size_str = model_info['size'].replace(' MB', '').replace(' GB', '')
        if 'GB' in model_info['size']:
            total_size += float(size_str) * 1024
        else:
            total_size += float(size_str)
    
    print(f"\n📊 Total download size: ~{total_size:.0f} MB")
    
    # Ask for confirmation
    response = input("\n🤔 Do you want to proceed with downloading? (y/N): ").lower().strip()
    if response not in ['y', 'yes']:
        print("❌ Download cancelled by user")
        return
    
    # Download missing models
    success_count = 0
    for model_name, model_info in missing_models:
        if download_file(model_info['url'], model_name, model_name):
            success_count += 1
        else:
            print(f"⚠️  You can manually download {model_name} from:")
            print(f"   {model_info['url']}")
    
    print(f"\n📈 Summary:")
    print(f"   • Successfully downloaded: {success_count}/{len(missing_models)} models")
    print(f"   • Already had: {len(existing_models)} models")
    
    if success_count == len(missing_models):
        print("\n🎉 All models downloaded successfully!")
        print("💡 You can now run the detection script:")
        print("   python detect_and_track.py --source your_video.mp4")
    else:
        print(f"\n⚠️  {len(missing_models) - success_count} models failed to download")
        print("   Please download them manually or check your internet connection")

if __name__ == "__main__":
    main()
