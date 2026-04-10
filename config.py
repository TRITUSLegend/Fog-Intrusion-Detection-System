"""
============================================================
  Configuration Module
  Fog-Assisted Real-Time Human Occupancy & Intrusion Detection
============================================================
Central configuration for all system parameters.
"""

import os

# ──────────────────────────────────────────────
#  Serial Communication (ESP32 Edge Layer)
# ──────────────────────────────────────────────
SERIAL_PORT = "COM3"          # Change to your ESP32 port (e.g., COM5 on Windows, /dev/ttyUSB0 on Linux)
SERIAL_BAUD = 115200          # Must match ESP32 baud rate

# ──────────────────────────────────────────────
#  Camera Settings
# ──────────────────────────────────────────────
CAMERA_INDEX = 0              # Default webcam
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# ──────────────────────────────────────────────
#  MobileNet-SSD Model Paths
# ──────────────────────────────────────────────
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")
PROTOTXT_PATH = os.path.join(MODEL_DIR, "MobileNetSSD_deploy.prototxt")
CAFFEMODEL_PATH = os.path.join(MODEL_DIR, "MobileNetSSD_deploy.caffemodel")

# Detection confidence threshold (0.0 - 1.0)
CONFIDENCE_THRESHOLD = 0.95

# ──────────────────────────────────────────────
#  Intrusion Image Saving
# ──────────────────────────────────────────────
IMG_SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
COOLDOWN_SECONDS = 5          # Minimum seconds between image captures

# ──────────────────────────────────────────────
#  LDR Light Classification Thresholds
#  ESP32 ADC mapping (based on current circuit): higher values = brighter
# ──────────────────────────────────────────────
LDR_DAY_THRESHOLD = 800       # Above this = Day (mapped from 0-1023)
LDR_DUSK_THRESHOLD = 500      # Between dusk and day = Dusk/Dawn
                              # Below dusk = Night

# ──────────────────────────────────────────────
#  MQTT Cloud Layer (organised topic hierarchy)
# ──────────────────────────────────────────────
MQTT_BROKER = "localhost"     # MQTT Explorer broker address
MQTT_PORT = 1883              # Default MQTT port
MQTT_CLIENT_ID = "fog_intrusion_detector"

# Topic hierarchy for clean MQTT Explorer dashboard:
#   fog/
#   ├── edge/
#   │   ├── motion        → PIR motion status
#   │   └── environment   → LDR light level + day/night
#   ├── detection/
#   │   ├── occupancy     → People count
#   │   └── intrusion     → Intrusion alert + image path
#   └── system/
#       └── status        → System heartbeat
MQTT_TOPIC_MOTION     = "fog/edge/motion"
MQTT_TOPIC_ENVIRONMENT = "fog/edge/environment"
MQTT_TOPIC_OCCUPANCY  = "fog/detection/occupancy"
MQTT_TOPIC_INTRUSION  = "fog/detection/intrusion"
MQTT_TOPIC_STATUS     = "fog/system/status"

# ──────────────────────────────────────────────
#  Display Settings
# ──────────────────────────────────────────────
WINDOW_NAME = "Fog Intrusion Detection System"
BOX_COLOR = (0, 255, 0)      # Green bounding boxes (BGR)
TEXT_COLOR = (0, 255, 0)      # Green text (BGR)
ALERT_COLOR = (0, 0, 255)    # Red alert text (BGR)
