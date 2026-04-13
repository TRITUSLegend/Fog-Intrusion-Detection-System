/*
 * ============================================================
 *   ESP32 Edge Layer – IoT Sensor Node
 *   Fog-Assisted Real-Time Human Occupancy & Intrusion Detection
 * ============================================================
 */

// ── Pin Definitions ──
#define PIR_PIN   27    // PIR motion sensor digital output
#define LDR_PIN   34    // LDR sensor (analog input, ADC1 channel)
#define LED_PIN   2     // Onboard LED status

// ── Timing ──
#define SEND_INTERVAL_MS   500   // Send sensor data every 500 ms
#define SAMPLE_INTERVAL_MS 30    // Sample PIR every 30ms for debouncing

unsigned long lastSendTime = 0;
unsigned long lastSampleTime = 0;

// ── Debouncing State ──
int pirDebounced = 0;
int highSampleCount = 0;
const int REQUIRED_SAMPLES = 5; // Must be HIGH for 150ms (5 * 30ms)

void setup() {
    // Initialise serial communication with fog node
    Serial.begin(115200);
    delay(1000);

    // Configure pins
    pinMode(PIR_PIN, INPUT_PULLDOWN); // Use Pulldown to prevent floating pin triggers
    pinMode(LED_PIN, OUTPUT);

    Serial.println("==================================");
    Serial.println("  ESP32 Edge Node – Sensors Ready");
    Serial.println("==================================");
}

void loop() {
    unsigned long currentTime = millis();

    // ── 1. High-Frequency PIR Sampling (Debouncing) ──
    if (currentTime - lastSampleTime >= SAMPLE_INTERVAL_MS) {
        lastSampleTime = currentTime;
        
        int rawState = digitalRead(PIR_PIN);
        
        if (rawState == HIGH) {
            highSampleCount++;
            if (highSampleCount >= REQUIRED_SAMPLES) {
                pirDebounced = 1;
                digitalWrite(LED_PIN, HIGH); // Instant visual feedback
                highSampleCount = REQUIRED_SAMPLES; // Cap count
            }
        } else {
            highSampleCount = 0;
            pirDebounced = 0;
            digitalWrite(LED_PIN, LOW);
        }
    }

    // ── 2. Reporting Loop (Communication with Fog Node) ──
    if (currentTime - lastSendTime >= SEND_INTERVAL_MS) {
        lastSendTime = currentTime;

        // Read LDR Light Sensor
        int ldrValue = analogRead(LDR_PIN);

        // Map LDR value to 0-1023 range (ESP32 is 12-bit, so 0-4095)
        int mappedLdr = map(ldrValue, 0, 4095, 0, 1023);
        
        // Output JSON format for MACF algorithm
        // Note: Using the debounced PIR state here
        Serial.print("{\"pir\":");
        Serial.print(pirDebounced);
        Serial.print(",\"ldr\":");
        Serial.print(mappedLdr);
        Serial.println("}");
    }
}
