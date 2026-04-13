# Fog-Assisted Real-Time Human Occupancy and Intrusion Detection System

## Using Edge Intelligence | MobileNet-SSD | ESP32 | MQTT

---

##  Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Setup Guide](#setup-guide)
- [Running the System](#running-the-system)
- [MQTT Cloud Dashboard](#mqtt-cloud-dashboard)
- [ESP32 Wiring Diagram](#esp32-wiring-diagram)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)

---

## Overview

This project implements a **fog computing** architecture for **real-time intrusion detection and occupancy counting**. An ESP32 microcontroller (edge layer) collects motion and light sensor data, while a PC (fog layer) runs a pretrained MobileNet-SSD deep learning model to detect and count humans in a live camera feed. Detection results are published via MQTT to a cloud dashboard.

### Key Features

- ✅ **Multi-Modal Adaptive Confidence Fusion (MACF)** for intelligent detection
- ✅ Real-time human detection using pretrained MobileNet-SSD (CPU-friendly)
- ✅ **Automated Evidence Capture**: Saves annotated frames when an intrusion is confirmed
- ✅ **Live Dashboard**: Real-time MQTT reporting for motion, light, and occupancy
- ✅ **Adaptive Logic**: Dynamic frame-differencing threshold based on ambient light (LDR)
- ✅ Fog computing architecture for low latency and privacy
- ✅ Cooldown timer to prevent duplicate captures and disk flooding
- ✅ Graceful recovery for hardware (Serial/Camera) disconnections

---

## System Architecture

```
┌─────────────────────┐     Serial      ┌──────────────────────────────────┐     MQTT     ┌──────────────────┐
│   EDGE LAYER        │  ──────────►    │        FOG LAYER                 │  ─────────►  │   CLOUD LAYER    │
│   (ESP32)           │     USB         │        (PC / Laptop)             │              │   (MQTT Explorer)│
│                     │                 │                                  │              │                  │
│  • PIR Motion Sensor│                 │  • OpenCV Video Capture          │              │  • fog/occupancy │
│  • LDR Light Sensor │                 │  • MobileNet-SSD Detection       │              │  • fog/intrusion │
│  • Serial Output    │                 │  • People Counting               │              │  • fog/sensor    │
│                     │                 │  • Intrusion Alerting            │              │                  │
│                     │                 │  • Image Saving (timestamped)    │              │                  │
└─────────────────────┘                 └──────────────────────────────────┘              └──────────────────┘
```

---

## Project Structure

```
FOG and EDGE COMPUTING project/
├── main.py                 # Central Fog layer orchestration
├── config.py               # System-wide configuration
├── detector.py             # Human detection using MobileNet-SSD
├── sensor_interface.py     # ESP32 Serial data management
├── macf_fusion.py          # MACF Fusion algorithm logic
├── alert_system.py         # Alert classification & evidence capture
├── video_processor.py      # Frame differencing & motion calculation
├── mqtt_client.py          # Cloud reporting (MQTT Explorer)
├── download_model.py       # (Optional) One-time model downloader
├── requirements.txt        # Python dependencies
├── README.md               # Documentation
│
├── model/                  # AI Model storage
│   ├── MobileNetSSD_deploy.prototxt
│   └── MobileNetSSD_deploy.caffemodel
│
├── img/                    # Evidence captures (automated)
│
└── esp32_edge/             # Edge Layer firmware
    └── esp32_edge.ino
```

---

## Hardware Requirements

| Component | Purpose | Pin |
|-----------|---------|-----|
| ESP32 Dev Board | Edge microcontroller | – |
| PIR Motion Sensor (HC-SR501) | Detect human motion | GPIO 27 |
| LDR Sensor Module | Measure ambient light | GPIO 34 (ADC) |
| USB Cable | Serial communication to PC | – |
| Webcam / Laptop Camera | Video feed for detection | – |

---

## Software Requirements

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.8+ | Fog node runtime |
| OpenCV | 4.5+ | Computer vision & ML inference |
| NumPy | 1.21+ | Numerical operations |
| PySerial | 3.5+ | ESP32 serial communication |
| paho-mqtt | 1.6+ | MQTT cloud publishing |
| Arduino IDE | 2.x | ESP32 firmware upload |
| MQTT Explorer | Latest | Cloud dashboard |

---

## Setup Guide

### Step 1: Install Python Dependencies

```bash
cd "FOG and EDGE COMPUTING project"
pip install -r requirements.txt
```

### Step 2: Download the ML Model

```bash
python download_model.py
```

This downloads:
- `MobileNetSSD_deploy.prototxt` (~28 KB) – Network architecture
- `MobileNetSSD_deploy.caffemodel` (~23 MB) – Pretrained weights

### Step 3: Upload ESP32 Firmware

1. Open `esp32_edge/esp32_edge.ino` in **Arduino IDE**
2. Select **Board**: ESP32 Dev Module
3. Select the correct **COM Port**
4. Click **Upload**

### Step 4: Wire the ESP32

See [Wiring Diagram](#esp32-wiring-diagram) below.

### Step 5: Configure the System

Edit `config.py` to match your setup:

```python
SERIAL_PORT = "COM8"      # ← Change to match your ESP32 (e.g., COM3, COM4)
CAMERA_INDEX = 0           # ← Change if using external webcam
MQTT_BROKER = "localhost"  # ← Change if broker is on another machine
```

### Step 6: Install and Start MQTT Explorer

1. Download from [mqtt-explorer.com](http://mqtt-explorer.com/)
2. Open MQTT Explorer
3. Connect to `localhost:1883`
4. You will see live, structured data on topics:
   - `fog/edge/motion`
   - `fog/edge/environment`
   - `fog/detection/occupancy`
   - `fog/detection/intrusion`
   - `fog/system/status`

If you don't have a broker installed, install **Mosquitto**:
```bash
# Windows: Download from https://mosquitto.org/download/
# Then start the service
net start mosquitto
```

---

## Running the System

### Full System (with ESP32 + MQTT)

```bash
python main.py
```

### Camera-Only Mode (no ESP32)

The system automatically falls back to camera-only mode if the ESP32 is not connected. It will assume motion is always detected and process every frame.

```bash
# Just run without ESP32 connected
python main.py
```

### Controls

- Press **`q`** in the camera window to quit
- Press **`Ctrl+C`** in the terminal to quit

---

The fog node publishes JSON data to these hierarchical MQTT topics:

### `fog/edge/motion`
```json
{
  "motion_detected": true,
  "status": "MOTION DETECTED",
  "timestamp": "17:30:00 07-04-2026"
}
```

### `fog/edge/environment`
```json
{
  "light_level_raw": 1000,
  "light_condition": "Day",
  "description": "Day (LDR: 1000)",
  "timestamp": "17:30:00 07-04-2026"
}
```

### `fog/detection/occupancy`
```json
{
  "people_count": 2,
  "status": "2 person(s) detected",
  "zone_status": "OCCUPIED",
  "timestamp": "17:30:00 07-04-2026"
}
```

### `fog/detection/intrusion`
```json
{
  "Timestamp": "2026-04-07T17:30:00",
  "IPS": 0.85,
  "Alert": "INTRUSION CONFIRMED",
  "Image_path": "img/intrusion_20260407_173000.jpg"
}
```

---

## ESP32 Wiring Diagram

```
                    ┌─────────────────────┐
                    │      ESP32          │
                    │                     │
   PIR Sensor ─────┤ GPIO 27        3V3  ├───── PIR VCC
                    │                     │
   LDR Module ─────┤ GPIO 34 (ADC)  GND  ├───── PIR GND + LDR GND
                    │                     │
                    │   USB ──► PC        │
                    └─────────────────────┘

PIR Sensor (HC-SR501):
  VCC  → ESP32 3.3V (or 5V via VIN)
  GND  → ESP32 GND
  OUT  → ESP32 GPIO 27

LDR Module:
  VCC  → ESP32 3.3V
  GND  → ESP32 GND
  AO   → ESP32 GPIO 34
```

---

## How It Works

### Processing Flow

```
1. ESP32 sends Motion + LDR data via Serial JSON
       ↓
2. MACF calculates Environmental Risk Factor (ERF) based on Light
       ↓
3. System adjusts Video Sensitivity (Tau) dynamically based on ERF
       ↓
4. Frame Difference + AI Detection calculates IPS (Intrusion Probability Score)
       ↓
5. Logic fuses PIR status with Visual/Environmental data
       ↓
6. If IPS ≥ 0.75: **Intrusion Confirmed** → Capture Evidence Image
       ↓
7. Publish Live Dashboard Data + Critical Alerts to Cloud via MQTT
```

### Key Design Decisions

- **MobileNet-SSD** was chosen because it runs at ~20+ FPS on CPU, making it ideal for fog computing where GPU is not available.
- **Cooldown timer** (5 seconds) prevents disk flooding from continuous detections.
- **Fallback mode** ensures the system works even without the ESP32 connected.
- **Modular architecture** separates detection, communication, saving, and publishing into independent modules.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Camera not opening | Check `CAMERA_INDEX` in `config.py`. Try `1` for external webcam |
| Serial port error | Verify COM port in Device Manager. **Close Arduino Serial Monitor** |
| Sensor Offline Status | Ensure ESP32 is plugged in and running the correct firmware |
| PIR/LDR Stuck at -1 | Connectivity issue. Check USB cable and `SERIAL_PORT` in `config.py` |
| Model not found | Run `python download_model.py` to download model files |
| MQTT not connecting | Ensure Mosquitto broker is running. Check `MQTT_BROKER` setting |
| Low FPS | Close other applications. The model is optimized for CPU |
| No detections | Lower `CONFIDENCE_THRESHOLD` in `config.py` (e.g., to `0.3`) |
| Multiple captures | Increase `COOLDOWN_SECONDS` in `config.py` |

---

## License

This project is created for academic and educational purposes as part of a Fog and Edge Computing course project.
