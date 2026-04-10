import cv2
import time

class VideoProcessor:
    def __init__(self, camera_index=0, width=640, height=480):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.cap = None
        self.F_prev = None
        self.initialize_camera()

    def initialize_camera(self):
        print(f"[INFO] Initializing webcam {self.camera_index}...")
        if self.cap is not None:
            self.cap.release()
            
        self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        if not self.cap.isOpened():
            print("[ERROR] Failed to open webcam!")
            self.cap = None
            return False

        # Read first frame and set F_prev
        ret, frame = self.cap.read()
        if ret:
            self.F_prev = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return True
        else:
            print("[ERROR] Failed to read initial frame from webcam.")
            return False

    def capture_and_process(self, tau_adaptive):
        """
        Capture current frame, compare with F_prev, return current frame, motion masks, and C_vid.
        """
        if self.cap is None or not self.cap.isOpened():
            print("[WARN] Camera unavailable, attempting reinitialization...")
            if not self.initialize_camera():
                return None, 0, 0.0

        ret, frame = self.cap.read()
        if not ret:
            print("[WARN] Failed to read frame.")
            return None, 0, 0.0

        # Convert to grayscale
        F_curr = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Ensure F_prev isn't None
        if self.F_prev is None:
            self.F_prev = F_curr
            return frame, 0, 0.0

        # Compute frame difference
        D = cv2.absdiff(F_curr, self.F_prev)

        # Apply threshold to create binary mask
        # cv2.threshold returns (retval, dst)
        _, B = cv2.threshold(D, tau_adaptive, 255, cv2.THRESH_BINARY)
        
        # B is typically 0 or 255. We want count of non-zero pixels.
        motion_pixels = cv2.countNonZero(B)
        
        # Compute video confidence
        c_vid = min(1.0, float(motion_pixels) / 5000.0)

        # Update F_prev
        self.F_prev = F_curr

        return frame, motion_pixels, c_vid

    def close(self):
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()
