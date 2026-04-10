"""
============================================================
  Model Downloader
  Downloads the MobileNet-SSD pretrained model files.
============================================================
Run this script ONCE before starting the system:
    python download_model.py
"""

import os
import urllib.request
import sys

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")

FILES = {
    "MobileNetSSD_deploy.prototxt": (
        "https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/"
        "master/voc/MobileNetSSD_deploy.prototxt"
    ),
    "MobileNetSSD_deploy.caffemodel": (
        "https://github.com/chuanqi305/MobileNet-SSD/raw/master/"
        "mobilenet_iter_73000.caffemodel"
    ),
}


def download_file(url, dest_path, filename):
    """Download a file with progress indication."""
    print(f"  Downloading {filename}...")
    print(f"    URL: {url}")

    try:
        def progress_hook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 / total_size)
                mb = downloaded / (1024 * 1024)
                total_mb = total_size / (1024 * 1024)
                sys.stdout.write(f"\r    Progress: {percent:.1f}% ({mb:.1f}/{total_mb:.1f} MB)")
                sys.stdout.flush()

        urllib.request.urlretrieve(url, dest_path, reporthook=progress_hook)
        print(f"\n    ✓ Saved to {dest_path}")
        return True
    except Exception as e:
        print(f"\n    ✗ Download failed: {e}")
        return False


def main():
    print("=" * 55)
    print("  MobileNet-SSD Model Downloader")
    print("=" * 55)

    os.makedirs(MODEL_DIR, exist_ok=True)
    print(f"\n  Model directory: {MODEL_DIR}\n")

    all_ok = True
    for filename, url in FILES.items():
        dest_path = os.path.join(MODEL_DIR, filename)

        if filename == "MobileNetSSD_deploy.caffemodel":
            # The GitHub raw URL redirects, so we save with our expected name
            dest_path = os.path.join(MODEL_DIR, "MobileNetSSD_deploy.caffemodel")

        if os.path.exists(dest_path):
            size_mb = os.path.getsize(dest_path) / (1024 * 1024)
            print(f"  ✓ {filename} already exists ({size_mb:.1f} MB). Skipping.")
            continue

        if not download_file(url, dest_path, filename):
            all_ok = False

    print()
    if all_ok:
        print("  All model files are ready!")
        print("  You can now run:  python main.py")
    else:
        print("  Some downloads failed. Please check your internet connection")
        print("  or download the files manually into the 'model/' folder.")
    print()


if __name__ == "__main__":
    main()
