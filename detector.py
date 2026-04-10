"""
============================================================
  Human Detection Module
  Fog-Assisted Real-Time Human Occupancy & Intrusion Detection
============================================================
Uses MobileNet-SSD pretrained model to detect and count humans
in video frames. Only the "person" class is considered.
"""

import cv2
import numpy as np
import config

# MobileNet-SSD class labels (21 classes from PASCAL VOC)
CLASSES = [
    "background", "aeroplane", "bicycle", "bird", "boat",
    "bottle", "bus", "car", "cat", "chair", "cow",
    "diningtable", "dog", "horse", "motorbike", "person",
    "pottedplant", "sheep", "sofa", "train", "tvmonitor"
]

# Index of "person" class
PERSON_CLASS_ID = CLASSES.index("person")


class HumanDetector:
    """
    Wraps the MobileNet-SSD Caffe model for person-only detection.
    Lightweight enough to run on CPU in real time.
    """

    def __init__(self):
        """Load the pretrained Caffe model from disk."""
        print("[INFO] Loading MobileNet-SSD model...")
        try:
            self.net = cv2.dnn.readNetFromCaffe(
                config.PROTOTXT_PATH,
                config.CAFFEMODEL_PATH
            )
            # Force CPU backend for broad compatibility
            self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            print("[INFO] Model loaded successfully.")
        except Exception as e:
            raise RuntimeError(
                f"[ERROR] Failed to load model. Ensure model files exist in "
                f"'{config.MODEL_DIR}'.\n  → {e}"
            )

    def detect(self, frame):
        """
        Run person detection on a single video frame.

        Parameters
        ----------
        frame : numpy.ndarray
            BGR image captured from camera.

        Returns
        -------
        detections : list of dict
            Each dict has keys: 'box' (x1, y1, x2, y2), 'confidence' (float).
        annotated_frame : numpy.ndarray
            Copy of input frame with bounding boxes and labels drawn.
        people_count : int
            Number of people detected above the confidence threshold.
        """
        h, w = frame.shape[:2]
        annotated = frame.copy()

        # Preprocess: resize to 300×300, mean subtraction, scale
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)),
            scalefactor=0.007843,
            size=(300, 300),
            mean=(127.5, 127.5, 127.5),
            swapRB=False,
            crop=False
        )
        self.net.setInput(blob)
        raw_detections = self.net.forward()

        detections = []
        people_count = 0

        for i in range(raw_detections.shape[2]):
            class_id = int(raw_detections[0, 0, i, 1])
            confidence = float(raw_detections[0, 0, i, 2])

            # Only consider "person" class above threshold
            if class_id != PERSON_CLASS_ID:
                continue
            if confidence < config.CONFIDENCE_THRESHOLD:
                continue

            people_count += 1

            # Scale bounding box back to original frame dimensions
            box = raw_detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            x1, y1, x2, y2 = box.astype("int")

            # Clamp coordinates to frame boundaries
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)

            detections.append({
                "box": (x1, y1, x2, y2),
                "confidence": confidence
            })

            # ── Draw bounding box ──
            cv2.rectangle(annotated, (x1, y1), (x2, y2),
                          config.BOX_COLOR, 2)

            # ── Draw label ──
            label = f"Person {confidence:.0%}"
            label_size, baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            # Background rectangle for readability
            cv2.rectangle(
                annotated,
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0], y1),
                config.BOX_COLOR, -1
            )
            cv2.putText(
                annotated, label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (255, 255, 255), 1, cv2.LINE_AA
            )

        # ── Overlay: People count ──
        # ── Annotations managed externally via main.py ──

        return detections, annotated, people_count
