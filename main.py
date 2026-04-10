import cv2
import time
import json
import traceback

import config
from sensor_interface import SensorInterface
from video_processor import VideoProcessor
from macf_fusion import MACFFusion
from alert_system import AlertSystem
from mqtt_client import MQTTPublisher
from detector import HumanDetector

def print_banner():
    banner = """
    ==========================================================
    MULTI-MODAL ADAPTIVE CONFIDENCE FUSION (MACF) SYSTEM
    ==========================================================
    Edge Layer: ESP32 (PIR + LDR)
    Fog Layer: Python MACF Fusion Node
    Cloud Layer: MQTT Output
    ==========================================================
    """
    print(banner)

def main():
    print_banner()

    # Initialize Modules
    sensor_iface = SensorInterface(port=config.SERIAL_PORT, baudrate=config.SERIAL_BAUD)
    vid_processor = VideoProcessor(camera_index=config.CAMERA_INDEX, width=config.FRAME_WIDTH, height=config.FRAME_HEIGHT)
    macf = MACFFusion(tau_base=25)
    mqtt_pub = MQTTPublisher()
    alert_sys = AlertSystem(log_path="macf_logs.csv", mqtt_publisher=mqtt_pub)
    human_detector = HumanDetector()
    
    print("\n[INFO] Starting continuous MACF loop... Press 'q' to exit.\n")
    
    prev_time = time.time()
    frame_count = 0
    fps = 0.0
    
    # Cache sensor values to avoid skipping frames if ESP32 disconnects
    pir_val = 0
    ldr_val = 1000

    try:
        while True:
            # ── 1. Sensor Data Acquisition ──
            sensor_data = sensor_iface.read_data()
            if sensor_data is not None:
                pir_val = sensor_data["pir"]
                ldr_val = sensor_data["ldr"]

            # ── Calculate ERF and Tau temporarily before Video Processing ──
            # Step 2 & 3 in fusion but tau is needed for video frame
            erf = macf.compute_erf(ldr_val)
            tau_adaptive = macf.compute_tau_adaptive(erf)

            # ── 5. Video Processing ──
            frame, motion_pixels, c_vid = vid_processor.capture_and_process(tau_adaptive)
            if frame is None:
                continue

            # ── 6 & 7. MACF Fusion ──
            # Compute final IPS based on PIR, LDR, and C_vid
            _, _, ips = macf.compute_fusion(pir_val, ldr_val, c_vid)

            # ── 7.5 Human Detection & Dashboard Updates ──
            detections, annotated_frame, people_count = human_detector.detect(frame)

            # Live MQTT Status updates (unconditional reporting for dashboard)
            mqtt_pub.publish_motion(pir_val == 1)
            mqtt_pub.publish_environment(ldr_val)
            if pir_val == 1:
                mqtt_pub.publish_occupancy(people_count)

            # ── Calculate FPS ──
            frame_count += 1
            current_time = time.time()
            elapsed = current_time - prev_time
            if elapsed >= 1.0:
                fps = frame_count / elapsed
                frame_count = 0
                prev_time = current_time

            # ── Output Display Overlay ──
            display_frame = annotated_frame
            
            # Colors based on alert
            if ips >= 0.75:
                color = (0, 0, 255) # Red
            elif ips >= 0.45:
                color = (0, 165, 255) # Orange
            else:
                color = (0, 255, 0) # Green

            # Overlay info
            cv2.putText(display_frame, f"System: MACF | People: {people_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(display_frame, f"IPS Score: {ips:.2f}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.putText(display_frame, f"Status: Active", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.putText(display_frame, f"Motion Pixels: {motion_pixels}", (10, config.FRAME_HEIGHT - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            cv2.putText(display_frame, f"PIR: {pir_val} | LDR: {ldr_val} | FPS: {fps:.1f}", (10, config.FRAME_HEIGHT - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

            # ── 8. Alert Classification & Logging / Network ──
            # Pass the annotated frame for evidence capture
            alert_status = alert_sys.process_alert(ips, pir_val, ldr_val, motion_pixels, display_frame)
            cv2.putText(display_frame, f"Alert: {alert_status}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            cv2.imshow("MACF Intrusion Detection", display_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[INFO] Exiting via Q key...")
                break

    except KeyboardInterrupt:
        print("\n[INFO] Keyboard Interrupt...")
    except Exception as e:
        print("\n[ERROR] Crashing exception in main loop:")
        traceback.print_exc()
    finally:
        sensor_iface.close()
        vid_processor.close()
        mqtt_pub.close()
        print("[INFO] Shutdown complete.")

if __name__ == "__main__":
    main()
