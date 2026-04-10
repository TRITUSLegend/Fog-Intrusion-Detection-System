"""
============================================================
  MQTT Cloud Layer Module
  Fog-Assisted Real-Time Human Occupancy & Intrusion Detection
============================================================
Publishes organised data to an MQTT broker (MQTT Explorer)
which serves as the cloud layer dashboard.

Topic Hierarchy:
  fog/
  ├── edge/
  │   ├── motion        → PIR motion status (detected / clear)
  │   └── environment   → LDR light + day/dusk/night classification
  ├── detection/
  │   ├── occupancy     → People count (only when motion detected)
  │   └── intrusion     → Intrusion alert + evidence image path
  └── system/
      └── status        → System heartbeat & uptime
"""

import json
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("[WARN] paho-mqtt not installed. MQTT publishing disabled.")
    print("       Install with: pip install paho-mqtt")

import config


def classify_light(ldr_value):
    """
    Classify ambient light from LDR analog value.

    ESP32 ADC: 0 (bright light) → 4095 (complete darkness)

    Returns
    -------
    str
        One of: 'Day', 'Dusk/Dawn', 'Night'
    """
    if ldr_value >= config.LDR_DAY_THRESHOLD:
        return "Day"
    elif ldr_value >= config.LDR_DUSK_THRESHOLD:
        return "Dusk/Dawn"
    else:
        return "Night"


class MQTTPublisher:
    """
    Publishes organised detection and sensor data to MQTT broker.
    Data is structured for clean display in MQTT Explorer dashboard.
    """

    def __init__(self):
        """Connect to the MQTT broker."""
        self.client = None
        self.connected = False
        self._start_time = datetime.now()

        if not MQTT_AVAILABLE:
            return

        try:
            # paho-mqtt v2 requires CallbackAPIVersion
            try:
                self.client = mqtt.Client(
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
                    client_id=config.MQTT_CLIENT_ID,
                    protocol=mqtt.MQTTv311
                )
            except (AttributeError, TypeError):
                # Fallback for paho-mqtt v1.x
                self.client = mqtt.Client(
                    client_id=config.MQTT_CLIENT_ID,
                    protocol=mqtt.MQTTv311
                )

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect

            print(f"[INFO] Connecting to MQTT broker at "
                  f"{config.MQTT_BROKER}:{config.MQTT_PORT}...")
            self.client.connect(config.MQTT_BROKER, config.MQTT_PORT, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            print(f"[WARN] MQTT connection failed: {e}")
            print("       System will continue without cloud publishing.")
            self.client = None

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker."""
        if rc == 0:
            self.connected = True
            print("[INFO] MQTT connected to broker successfully.")
            # Publish system online status
            self.publish_system_status("ONLINE")
        else:
            print(f"[WARN] MQTT connection returned code {rc}.")

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker."""
        self.connected = False
        if rc != 0:
            print("[WARN] MQTT unexpected disconnection.")

    # ─────────────────────────────────────────────
    #  Edge Layer Topics
    # ─────────────────────────────────────────────

    def publish_motion(self, motion_detected):
        """
        Publish PIR motion sensor status.
        Topic: fog/edge/motion
        """
        payload = {
            "motion_detected": motion_detected,
            "status": "MOTION DETECTED" if motion_detected else "No Motion",
            "timestamp": datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        }
        self._publish(config.MQTT_TOPIC_MOTION, payload)

    def publish_environment(self, ldr_value):
        """
        Publish LDR light data with day/night classification.
        Topic: fog/edge/environment
        """
        light_condition = classify_light(ldr_value)
        payload = {
            "light_level_raw": ldr_value,
            "light_condition": light_condition,
            "description": f"{light_condition} (LDR: {ldr_value})",
            "timestamp": datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        }
        self._publish(config.MQTT_TOPIC_ENVIRONMENT, payload)

    # ─────────────────────────────────────────────
    #  Detection Layer Topics (only when motion)
    # ─────────────────────────────────────────────

    def publish_occupancy(self, people_count):
        """
        Publish occupancy count (only called when motion detected).
        Topic: fog/detection/occupancy
        """
        payload = {
            "people_count": people_count,
            "status": f"{people_count} person(s) detected" if people_count > 0 else "Area Clear",
            "zone_status": "OCCUPIED" if people_count > 0 else "CLEAR",
            "timestamp": datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        }
        self._publish(config.MQTT_TOPIC_OCCUPANCY, payload)

    def publish_macf_alert(self, payload):
        """
        Publish an aggregate MACF intrusion alert payload.
        Topic: fog/detection/intrusion
        """
        self._publish(config.MQTT_TOPIC_INTRUSION, payload)

    # ─────────────────────────────────────────────
    #  System Topics
    # ─────────────────────────────────────────────

    def publish_system_status(self, status="ONLINE"):
        """
        Publish system heartbeat status.
        Topic: fog/system/status
        """
        uptime = (datetime.now() - self._start_time).total_seconds()
        payload = {
            "system_status": status,
            "uptime_seconds": round(uptime),
            "fog_node": "Active",
            "edge_device": "ESP32 (COM3)",
            "model": "MobileNet-SSD",
            "timestamp": datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        }
        self._publish(config.MQTT_TOPIC_STATUS, payload)

    # ─────────────────────────────────────────────
    #  Internal Helpers
    # ─────────────────────────────────────────────

    def _publish(self, topic, payload):
        """Internal helper to publish JSON payload to a topic."""
        if self.client is None or not self.connected:
            return
        try:
            msg = json.dumps(payload, indent=2)
            self.client.publish(topic, msg, qos=1)
        except Exception as e:
            print(f"[WARN] MQTT publish error on {topic}: {e}")

    def close(self):
        """Gracefully disconnect from the MQTT broker."""
        if self.client and self.connected:
            self.publish_system_status("OFFLINE")
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            print("[INFO] MQTT client disconnected.")
