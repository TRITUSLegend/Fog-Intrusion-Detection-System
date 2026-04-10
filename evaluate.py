import os
import time
import urllib.request

import cv2
import numpy as np

import config
config.CONFIDENCE_THRESHOLD = 0.40

from macf_fusion import MACFFusion
from detector import HumanDetector
from alert_system import AlertSystem

VIDEO_URL = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/vtest.avi"
VIDEO_PATH = "vtest.avi"

def download_video():
    if not os.path.exists(VIDEO_PATH):
        print("[INFO] Downloading OpenCV pedestrian dataset (vtest.avi)...")
        urllib.request.urlretrieve(VIDEO_URL, VIDEO_PATH)
        print("[INFO] Download complete.")

def evaluate():
    download_video()
    
    print("[INFO] Initializing algorithms for offline multi-case evaluation...")
    macf = MACFFusion(tau_base=25)
    human_detector = HumanDetector()
    alert_sys = AlertSystem(log_path="eval_logs_extended.csv")
    
    cap = cv2.VideoCapture(VIDEO_PATH)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[INFO] Started processing {total_frames} frames asynchronously.")

    start_time = time.time()
    
    # 8 Test Cases
    test_cases = [
        {"name": "TC1: Day Intrusion (Ideal)", "pir": 1, "ldr": 1000, "blank": False},
        {"name": "TC2: Night Intrusion (Low Light)", "pir": 1, "ldr": 50, "blank": False},
        {"name": "TC3: Day Visual-Only (Missing Thermal)", "pir": 0, "ldr": 800, "blank": False},
        {"name": "TC4: Night Visual-Only (Missing Thermal)", "pir": 0, "ldr": 50, "blank": False},
        {"name": "TC5: Day Thermal-Only (No Video Motion)", "pir": 1, "ldr": 900, "blank": True},
        {"name": "TC6: Night Thermal-Only (No Video Motion)", "pir": 1, "ldr": 20, "blank": True},
        {"name": "TC7: Day Completely Clear", "pir": 0, "ldr": 1000, "blank": True},
        {"name": "TC8: Night Completely Clear", "pir": 0, "ldr": 10, "blank": True},
    ]

    metrics = {tc["name"]: {"alerts": 0, "max_ips": 0.0, "total_people": 0, "frames": 0, "avg_ips": 0.0, "total_ips": 0.0, "tc_info": tc} for tc in test_cases}

    F_prev = None
    frame_idx = 0
    chunk_size = total_frames // len(test_cases)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Determine testcase chunk
        tc_idx = min(frame_idx // chunk_size, len(test_cases) - 1)
        current_tc = test_cases[tc_idx]
        phase_key = current_tc["name"]
        
        pir_val = current_tc["pir"]
        ldr_val = current_tc["ldr"]
        
        # Simulate Blank frames for cases where Video Motion is missing (e.g. thermal trigger but no visual)
        if current_tc["blank"]:
            frame = np.zeros_like(frame)

        # 1. ERF and Adaptive Tau 
        erf = macf.compute_erf(ldr_val)
        tau_adaptive = macf.compute_tau_adaptive(erf)
        
        # 2. Video Diff processing
        F_curr = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if F_prev is None:
            F_prev = F_curr
            frame_idx += 1
            continue
            
        D = cv2.absdiff(F_curr, F_prev)
        _, B = cv2.threshold(D, tau_adaptive, 255, cv2.THRESH_BINARY)
        motion_pixels = cv2.countNonZero(B)
        c_vid = min(1.0, float(motion_pixels) / 5000.0)
        
        F_prev = F_curr
        
        # 3. DNN Human Detection
        _, _, people_count = human_detector.detect(frame)
        
        # 4. IPS Processing
        _, _, ips = macf.compute_fusion(pir_val, ldr_val, c_vid)
        
        if ips >= 0.75:
            metrics[phase_key]["alerts"] += 1
            
        if ips > metrics[phase_key]["max_ips"]:
            metrics[phase_key]["max_ips"] = ips
            
        metrics[phase_key]["total_people"] += people_count
        metrics[phase_key]["frames"] += 1
        metrics[phase_key]["total_ips"] += ips
        
        frame_idx += 1

    cap.release()
    total_time = time.time() - start_time
    fps = total_frames / total_time

    print("====================================")
    print("      EVALUATION RESULTS            ")
    print("====================================")
    print(f"Total Time: {total_time:.2f} s")
    print(f"Simulation FPS: {fps:.2f} fps")
    
    for k, v in metrics.items():
        frames = v["frames"]
        if frames == 0: continue
        avg_people = v["total_people"] / frames
        v["avg_ips"] = v["total_ips"] / frames
        
        print(f"\n--- {k} ---")
        print(f"Max IPS Reached: {v['max_ips']:.2f}")
        print(f"Average IPS: {v['avg_ips']:.2f}")
        print(f"Intrusion Alert Frames: {v['alerts']}")
        print(f"Average Detected Humans/Frame: {avg_people:.2f}")

if __name__ == "__main__":
    evaluate()
