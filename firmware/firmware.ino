#include <PN5180.h>
#include <PN5180ISO14443.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// --- DISPLAY CONFIGURATION ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
// Map the OLED to our new safe pins
#define OLED_SDA 25
#define OLED_SCL 26
#define OLED_PWR 32 // Our custom power pin for the screen!

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// --- NETWORK CONFIGURATION ---
const char *ssid = "404NOTFOUND";
const char *password = "Batatinha123";
const char *serverUrl = "http://192.168.2.174:5000/api/tag_event";
const int sensorId = 1;

// --- PN5180 CONFIGURATION ---
#define PN5180_NSS 5
#define PN5180_BUSY 22
#define PN5180_RST 21
PN5180ISO14443 nfc(PN5180_NSS, PN5180_BUSY, PN5180_RST);

bool tagPresent = false;
uint8_t currentUid[10];
uint8_t currentUidLength = 0;
int missCount = 0;
int dotCounter = 0;

// Helper function to update the OLED screen text easily
void updateScreen(String line1, String line2 = "", String line3 = "")
{
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println(line1);
  if (line2 != "")
    display.println(line2);
  if (line3 != "")
    display.println(line3);
  display.display();
}

void setupWiFi()
{
  updateScreen("Connecting WiFi...", ssid);
  Serial.print("Connecting to WiFi...");

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected.");
  updateScreen("WiFi Connected!", WiFi.localIP().toString());
  delay(1500); // Hold the success message on screen for a moment
}

void sendTagEvent(String uid, String event)
{
  if (WiFi.status() == WL_CONNECTED)
  {
    updateScreen("Tag: " + uid, "Status: " + event, "Sending to DB...");

    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    String jsonPayload = "{\"epc_tag\": \"" + uid + "\", \"sensor_id\": " + String(sensorId) + ", \"event\": \"" + event + "\", \"rssi\": 0}";

    int httpResponseCode = http.POST(jsonPayload);

    if (httpResponseCode > 0)
    {
      Serial.println("HTTP Response code: " + String(httpResponseCode));
      updateScreen("Tag: " + uid, "Status: " + event, "DB Sync: SUCCESS");
    }
    else
    {
      Serial.println("Error code: " + String(httpResponseCode));
      updateScreen("Tag: " + uid, "Status: " + event, "DB Sync: FAILED");
    }
    http.end();
  }
  else
  {
    Serial.println("WiFi Disconnected");
    updateScreen("WiFi Error!", "Cannot sync DB");
  }
}

String uidToString(uint8_t *uid, uint8_t length)
{
  String s = "";
  for (int i = 0; i < length; i++)
  {
    if (uid[i] < 0x10)
      s += "0";
    s += String(uid[i], HEX);
  }
  s.toUpperCase();
  return s;
}

void setup()
{
  setCpuFrequencyMhz(80);
  Serial.begin(115200);

  // 1. TURN ON THE SCREEN'S POWER FIRST
  pinMode(OLED_PWR, OUTPUT);
  digitalWrite(OLED_PWR, HIGH);
  delay(100); // Give the screen a moment to power up

  // 2. INITIALIZE THE SCREEN ON THE NEW PINS
  Wire.begin(OLED_SDA, OLED_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C))
  {
    Serial.println(F("SSD1306 allocation failed"));
    for (;;)
      ; // Don't proceed, loop forever
  }

  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  updateScreen("Booting System...");
  delay(1000);

  // 3. START WIFI
  setupWiFi();

  // 4. START NFC
  updateScreen("Starting NFC...");
  nfc.begin();
  nfc.reset();
  nfc.setupRF();

  Serial.println("Initialization complete. Bring your MIFARE tag near...");
  updateScreen("System Ready", "Waiting for Tag...");
}

void loop()
{
  uint8_t uid[10];
  uint8_t uidLength = nfc.readCardSerial(uid);

  if (uidLength > 0 && uid[0] != 0x00)
  {
    missCount = 0;

    if (!tagPresent)
    {
      tagPresent = true;
      currentUidLength = uidLength;
      for (int i = 0; i < uidLength; i++)
        currentUid[i] = uid[i];

      String uidStr = uidToString(currentUid, currentUidLength);
      Serial.println("\n>>> TAG ARRIVED! UID: " + uidStr);

      // Sends HTTP request and updates screen
      sendTagEvent(uidStr, "ARRIVED");
    }
    else
    {
      Serial.print("h");
    }
  }
  else
  {
    if (tagPresent)
    {
      missCount++;
      if (missCount >= 3)
      {
        tagPresent = false;

        String uidStr = uidToString(currentUid, currentUidLength);
        Serial.println("\n<<< TAG REMOVED!");

        // Sends HTTP request and updates screen
        sendTagEvent(uidStr, "REMOVED");

        delay(1000); // Let the user see the "Removed" message
        currentUidLength = 0;
        updateScreen("System Ready", "Waiting for Tag...");
      }
    }
    else
    {
      // Background heartbeat
      dotCounter++;
      if (dotCounter >= 10)
      {
        Serial.print(".");
        dotCounter = 0;
      }
    }
  }
  delay(50);
}