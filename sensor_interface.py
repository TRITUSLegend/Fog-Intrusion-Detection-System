import serial
import json
import time

class SensorInterface:
    def __init__(self, port="COM3", baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.buffer = "" # Add internal buffer for partial lines
        self.last_attempt_time = 0.0
        self.last_packet_time = 0.0 # Time we last got a valid JSON
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
            self.buffer = "" # Clear buffer on reconnect
            print(f"[INFO] Serial: Connected to {self.port} at {self.baudrate} baud.")
            return True
        except serial.SerialException as e:
            print(f"[ERROR] Serial connection failed on {self.port}: {e}")
            if "PermissionError" in str(e):
                print("        TIP: Is the Arduino Serial Monitor still open? Please close it.")
            self.serial_conn = None
            return False

    def read_data(self):
        """
        Reads ALL available data from the serial buffer, finds the LATEST complete JSON.
        Returns:
            dict: {"pir": int, "ldr": int} or None if failed to find a valid packet.
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            if not self.connect():
                return None

        latest_packet = None

        try:
            # 1. Read everything currently in the serial driver's buffer
            chunk = self.serial_conn.read_all().decode('utf-8', errors='ignore')
            if chunk:
                self.buffer += chunk

            # 2. Extract all complete lines from our local buffer
            if "\n" in self.buffer:
                lines = self.buffer.split("\n")
                
                # The last element in 'lines' is either empty (if buffer ended in \n)
                # or a partial line (if it didn't). Keep it for the next call.
                self.buffer = lines.pop()

                # 3. Iterate through all complete lines and try to find the newest valid JSON
                # We iterate backwards (newest first) for efficiency
                for line in reversed(lines):
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        data = json.loads(line)
                        pir_val = data.get("pir")
                        ldr_val = data.get("ldr")
                        
                        # Validate the JSON structure
                        if pir_val is not None and ldr_val is not None:
                            latest_packet = {"pir": pir_val, "ldr": ldr_val}
                            self.last_packet_time = time.time()
                            break # Found the latest valid one, skip older ones
                    except json.JSONDecodeError as jde:
                        # Only log if it looks like it was meant to be JSON
                        if "{" in line:
                            print(f"[DEBUG] JSON Decode Error on line: {line[:50]}... Error: {jde}")
                        continue 
            
        except (serial.SerialException, UnicodeDecodeError) as e:
            print(f"[ERROR] Serial read error: {e}")
            self.serial_conn.close()
            self.serial_conn = None
            
        return latest_packet

    def close(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("[INFO] Serial connection closed.")
