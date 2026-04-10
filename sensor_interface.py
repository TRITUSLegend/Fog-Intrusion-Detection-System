import serial
import json
import time

class SensorInterface:
    def __init__(self, port="COM3", baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.last_attempt_time = 0.0
        self.connect_interval = 2.0  # seconds between reconnect attempts
        self.connect()

    def connect(self):
        """Attempt to establish serial connection non-blockingly."""
        current_time = time.time()
        
        # Prevent spamming connection attempts and blocking the video stream
        if current_time - self.last_attempt_time < self.connect_interval:
            return False
            
        self.last_attempt_time = current_time
        
        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                
            # Use timeout=0 so normal reads don't block the video either
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=0)
            print(f"[INFO] Connected to ESP32 on {self.port} at {self.baudrate} baud.")
            return True
        except serial.SerialException as e:
            # We don't print on every failure to prevent terminal spam
            self.serial_conn = None
            return False
    def read_data(self):
        """
        Reads one complete line from the serial buffer, parses JSON.
        Returns:
            dict: {"pir": int, "ldr": int} or None if failed.
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            self.connect()
            if not self.serial_conn:
                return None

        try:
            if self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode('utf-8').strip()
                if not line:
                    return None
                
                # Try to parse the JSON format
                data = json.loads(line)
                
                # Validate contents
                pir_val = data.get("pir")
                ldr_val = data.get("ldr")
                
                if pir_val not in (0, 1) or not (0 <= ldr_val <= 1023):
                    print(f"[WARN] Invalid sensor data values: {data}")
                    return None
                    
                return {"pir": pir_val, "ldr": ldr_val}
            
        except json.JSONDecodeError:
            pass # Handle corrupted/partial JSON gracefully by skipping
        except (serial.SerialException, UnicodeDecodeError) as e:
            print(f"[ERROR] Serial read error: {e}")
            self.serial_conn.close()
            self.serial_conn = None
            
        return None

    def close(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("[INFO] Serial connection closed.")
