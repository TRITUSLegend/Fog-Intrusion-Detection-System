/*
 * ============================================================
 *   ESP32 Edge Layer – IoT Sensor Node
 *   Fog-Assisted Real-Time Human Occupancy & Intrusion Detection
 * ============================================================
 *
 * Hardware:
 *   - ESP32 Development Board
 *   - PIR Motion Sensor  → GPIO 27
 *   - LDR Light Sensor   → GPIO 34 (ADC)
 *
 * Communication:
 *   - Sends sensor data over USB Serial at 115200 baud
 *   - Format:  Motion:0  or  Motion:1
 *              LDR:<analog_value>
 *
 * Upload this sketch to the ESP32 using Arduino IDE or PlatformIO.
 * ============================================================
 */

// ── Pin Definitions ──
#define PIR_PIN   27    // PIR motion sensor digital output
#define LDR_PIN   34    // LDR sensor (analog input, ADC1 channel)

// ── Timing ──
#define SEND_INTERVAL_MS  500   // Send sensor data every 500 ms

unsigned long lastSendTime = 0;

void setup() {
    // Initialise serial communication with fog node
    Serial.begin(115200);
    delay(1000);

    // Configure pins
    pinMode(PIR_PIN, INPUT);
     pinMode(2, OUTPUT);
    // LDR_PIN is analog, no need to set mode on ESP32

    Serial.println("==================================");
    Serial.println("  ESP32 Edge Node – Sensors Ready");
    Serial.println("==================================");
}

void loop() {
    unsigned long currentTime = millis();

    // Send sensor readings at regular intervals
    if (currentTime - lastSendTime >= SEND_INTERVAL_MS) {
        lastSendTime = currentTime;

        // ── Read PIR Motion Sensor ──
        int motionState = digitalRead(PIR_PIN);

        // ── Read LDR Light Sensor ──
        int ldrValue = analogRead(LDR_PIN);

        // ── Map LDR value to 0-1023 range ──
        int mappedLdr = map(ldrValue, 0, 4095, 0, 1023);

        // ── Send data to fog node via serial ──
        if(motionState==HIGH){
            digitalWrite(2,HIGH);
        }
        else{
            digitalWrite(2,LOW);
        }
        
        // Output JSON format for MACF algorithm
        Serial.print("{\"pir\":");
        Serial.print(motionState);
        Serial.print(",\"ldr\":");
        Serial.print(mappedLdr);
        Serial.println("}");
    }
}
