/**
 * VoiceMind ESP32 Audio Recorder
 * Captures audio from INMP441 I2S microphone and streams to server
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <esp32-hal-i2s.h>

// ============================================================================
// CONFIGURATION - UPDATE THESE VALUES
// ============================================================================

// WiFi Credentials
const char* ssid = "TSAPJK22_5GHz";
const char* password = "InD12:fdG!9";

// Server Configuration
const char* serverUrl = "http://192.168.1.100:8000";  // Change to your server IP
String meetingId = "";

// I2S Pin Configuration (INMP441)
#define I2S_WS 25        // Word Select (LRCLK)
#define I2S_SD 32        // Serial Data (DOUT)
#define I2S_SCK 33       // Serial Clock (BCLK)
#define I2S_PORT I2S_NUM_0

// Audio Configuration
#define SAMPLE_RATE 16000
#define BITS_PER_SAMPLE I2S_BITS_PER_SAMPLE_16BIT
#define BUFFER_SIZE 1024
#define CHUNK_SIZE 32000  // ~2 seconds at 16kHz (32000 bytes = 16000 samples)

// GPIO Pins
#define LED_PIN 2
#define BUTTON_PIN 4

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

bool isRecording = false;
int chunkCounter = 0;
uint8_t audioBuffer[CHUNK_SIZE];
int bufferIndex = 0;

// ============================================================================
// SETUP
// ============================================================================

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n===================================");
  Serial.println("VoiceMind ESP32 Audio Recorder");
  Serial.println("===================================\n");
  
  // Initialize GPIO
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  digitalWrite(LED_PIN, LOW);
  
  // Connect to WiFi
  connectWiFi();
  
  // Setup I2S
  setupI2S();
  
  Serial.println("✓ System Ready!");
  Serial.println("Press button to start/stop recording\n");
  
  // Blink LED to indicate ready
  blinkLED(3, 200);
}

// ============================================================================
// MAIN LOOP
// ============================================================================

void loop() {
  // Check button press (with debouncing)
  static unsigned long lastButtonPress = 0;
  if (digitalRead(BUTTON_PIN) == LOW && (millis() - lastButtonPress) > 300) {
    lastButtonPress = millis();
    
    isRecording = !isRecording;
    
    if (isRecording) {
      startRecording();
    } else {
      stopRecording();
    }
    
    // Wait for button release
    while (digitalRead(BUTTON_PIN) == LOW) {
      delay(10);
    }
  }
  
  // Record and stream audio if recording is active
  if (isRecording) {
    recordAndStream();
  }
}

// ============================================================================
// WIFI CONNECTION
// ============================================================================

void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal Strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm\n");
  } else {
    Serial.println("\n✗ WiFi Connection Failed!");
    Serial.println("Please check your credentials and try again.");
    while (true) {
      blinkLED(5, 100);  // Fast blink to indicate error
      delay(1000);
    }
  }
}

// ============================================================================
// I2S SETUP
// ============================================================================

void setupI2S() {
  Serial.println("Configuring I2S...");
  
  // I2S configuration
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = BITS_PER_SAMPLE,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = BUFFER_SIZE,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };
  
  // Pin configuration
  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };
  
  // Install and set pin config
  esp_err_t err = i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
  if (err != ESP_OK) {
    Serial.printf("✗ Failed to install I2S driver: %d\n", err);
    return;
  }
  
  err = i2s_set_pin(I2S_PORT, &pin_config);
  if (err != ESP_OK) {
    Serial.printf("✗ Failed to set I2S pins: %d\n", err);
    return;
  }
  
  i2s_zero_dma_buffer(I2S_PORT);
  
  Serial.println("✓ I2S Configured Successfully\n");
}

// ============================================================================
// RECORDING FUNCTIONS
// ============================================================================

void startRecording() {
  Serial.println("\n╔══════════════════════════════════╗");
  Serial.println("║   RECORDING STARTED              ║");
  Serial.println("╚══════════════════════════════════╝\n");
  
  digitalWrite(LED_PIN, HIGH);
  
  // Generate unique meeting ID
  meetingId = "meeting_" + String(millis());
  chunkCounter = 0;
  bufferIndex = 0;
  
  // Notify server about new meeting
  HTTPClient http;
  String url = String(serverUrl) + "/api/start_meeting?meeting_id=" + meetingId;
  http.begin(url);
  
  int httpCode = http.POST("");
  
  if (httpCode == 200) {
    Serial.println("✓ Meeting session created on server");
    Serial.println("Meeting ID: " + meetingId + "\n");
  } else {
    Serial.printf("✗ Failed to start meeting on server: HTTP %d\n\n", httpCode);
  }
  
  http.end();
}

void stopRecording() {
  Serial.println("\n╔══════════════════════════════════╗");
  Serial.println("║   RECORDING STOPPED              ║");
  Serial.println("╚══════════════════════════════════╝\n");
  
  digitalWrite(LED_PIN, LOW);
  
  // Send any remaining data in buffer
  if (bufferIndex > 0) {
    sendAudioChunk(audioBuffer, bufferIndex);
  }
  
  // Notify server about meeting end
  HTTPClient http;
  String url = String(serverUrl) + "/api/end_meeting?meeting_id=" + meetingId;
  http.begin(url);
  
  int httpCode = http.POST("");
  
  if (httpCode == 200) {
    Serial.println("✓ Meeting ended on server");
    Serial.println("Processing transcript and summary...\n");
  } else {
    Serial.printf("✗ Failed to end meeting on server: HTTP %d\n\n", httpCode);
  }
  
  http.end();
  
  Serial.printf("Total chunks sent: %d\n", chunkCounter);
  Serial.printf("Approximate duration: %.1f seconds\n\n", (chunkCounter * 2.0));
}

void recordAndStream() {
  uint8_t tempBuffer[BUFFER_SIZE];
  size_t bytesRead = 0;
  
  // Read audio data from I2S
  esp_err_t result = i2s_read(I2S_PORT, tempBuffer, BUFFER_SIZE, &bytesRead, portMAX_DELAY);
  
  if (result != ESP_OK) {
    Serial.printf("✗ I2S read error: %d\n", result);
    return;
  }
  
  // Accumulate data into chunk buffer
  for (size_t i = 0; i < bytesRead && bufferIndex < CHUNK_SIZE; i++) {
    audioBuffer[bufferIndex++] = tempBuffer[i];
  }
  
  // When chunk is full, send to server
  if (bufferIndex >= CHUNK_SIZE) {
    sendAudioChunk(audioBuffer, bufferIndex);
    bufferIndex = 0;
    chunkCounter++;
  }
}

void sendAudioChunk(uint8_t* data, int length) {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("✗ WiFi disconnected! Attempting to reconnect...");
    connectWiFi();
    return;
  }
  
  HTTPClient http;
  String url = String(serverUrl) + "/api/upload_audio";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/octet-stream");
  http.addHeader("X-Meeting-ID", meetingId);
  http.addHeader("X-Chunk-Number", String(chunkCounter));
  http.addHeader("X-Timestamp", String(millis()));
  http.addHeader("X-Sample-Rate", String(SAMPLE_RATE));
  
  int httpCode = http.POST(data, length);
  
  if (httpCode == 200) {
    Serial.printf("✓ Chunk %d sent (%d bytes)\n", chunkCounter, length);
    
    // Quick LED blink to indicate successful transmission
    digitalWrite(LED_PIN, LOW);
    delay(50);
    digitalWrite(LED_PIN, HIGH);
  } else {
    Serial.printf("✗ Error sending chunk %d: HTTP %d\n", chunkCounter, httpCode);
  }
  
  http.end();
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

void blinkLED(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(delayMs);
    digitalWrite(LED_PIN, LOW);
    delay(delayMs);
  }
}
