import csv
import datetime
import os
import cv2
import time
import config

class AlertSystem:
    def __init__(self, log_path="macf_logs.csv", mqtt_publisher=None):
        self.log_path = log_path
        self.mqtt_publisher = mqtt_publisher
        self.last_capture_time = 0
        self._initialize_log()

    def _initialize_log(self):
        # Create CSV with headers if it doesn't exist
        if not os.path.exists(self.log_path):
            with open(self.log_path, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "IPS", "PIR_val", "LDR_val", "Motion_pixels", "Alert"])

    def classify_alert(self, ips):
        if ips >= 0.75:
            return "INTRUSION CONFIRMED"
        elif ips >= 0.45:
            return "ELEVATED — MONITORING"
        else:
            return "CLEAR"

    def process_alert(self, ips, pir_val, ldr_val, motion_pixels, frame=None):
        """
        Classifies current state, handles logging and cloud transmission if needed.
        Returns the alert string.
        """
        alert = self.classify_alert(ips)
        image_path = None

        if ips >= 0.75:
            now = datetime.datetime.now()
            timestamp = now.isoformat()
            
            # --- Image Capture Logic ---
            if frame is not None:
                current_time = time.time()
                if current_time - self.last_capture_time >= config.COOLDOWN_SECONDS:
                    os.makedirs(config.IMG_SAVE_DIR, exist_ok=True)
                    filename = f"intrusion_{now.strftime('%Y%md_%H%M%S')}.jpg"
                    filepath = os.path.join(config.IMG_SAVE_DIR, filename)
                    
                    if cv2.imwrite(filepath, frame):
                        image_path = filepath
                        self.last_capture_time = current_time
                        print(f"[INFO] Intrusion image saved: {filepath}")

            # Log to CSV
            with open(self.log_path, mode="a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([timestamp, f"{ips:.2f}", pir_val, ldr_val, motion_pixels, alert])
            
            # Non-blocking network communication via MQTT
            if self.mqtt_publisher:
                payload = {
                    "Timestamp": timestamp,
                    "IPS": round(ips, 2),
                    "Alert": alert,
                    "Image_path": image_path if image_path else "No capture (cooldown)"
                }
                try:
                    self.mqtt_publisher.publish_macf_alert(payload)
                except Exception as e:
                    print(f"[WARN] Failed to transmit alert over MQTT: {e}")

        return alert
