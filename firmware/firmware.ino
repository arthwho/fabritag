#include <PN5180.h>
#include <PN5180ISO14443.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <WiFiManager.h>
#include <Preferences.h>

// --- DISPLAY CONFIGURATION ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define OLED_SDA 25
#define OLED_SCL 26
#define OLED_PWR 32
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// --- HARDWARE PINS ---
#define LED_PIN 2

// --- NETWORK & API CONFIGURATION ---
String serverUrl = "http://192.168.2.174:5000/api/tag_event";
String sensorId = "1";
bool isWifiConnected = false;
bool shouldSaveConfig = false;

// --- HEARTBEAT TIMER ---
unsigned long previousPingMillis = 0;
const unsigned long pingInterval = 10000;

// --- ADMIN RESET TAG ---
// Replace this with the exact UID of the tag you want to use as a master reset key
const String ADMIN_TAG_UID = "ABE06806";

// --- PN5180 CONFIGURATION ---
#define PN5180_NSS 5
#define PN5180_BUSY 22
#define PN5180_RST 21
#define PN5180_SCK 18
#define PN5180_MISO 19
#define PN5180_MOSI 23
PN5180ISO14443 nfc(PN5180_NSS, PN5180_BUSY, PN5180_RST);

// --- STATE VARIABLES ---
bool tagPresent = false;
bool nfcReady = false;
uint8_t currentUid[10];
uint8_t currentUidLength = 0;
int missCount = 0;
int idleMissCount = 0;
unsigned long lastPresentLogMillis = 0;
const int tagRemovedMissLimit = 3;
const int nfcRecoveryMissLimit = 25;
const unsigned long presentLogInterval = 2000;

// --- CUSTOM PORTAL CSS ---
const char *customPortalCSS =
    "<title>Fabritag Manager</title>"
    "<style>"
    "button, input[type='button'], input[type='submit'] {"
    "  background-color: #FF8C00 !important;"
    "  border: none !important;"
    "}"
    "button:hover, input[type='button']:hover, input[type='submit']:hover {"
    "  background-color: #E67E00 !important;"
    "}"
    "</style>";

// --- GLOBAL WIFIMANAGER PARAMETERS ---
WiFiManagerParameter custom_server_url("serverUrl", "Backend Server URL", "", 60);
WiFiManagerParameter custom_sensor_id("sensorId", "Sensor ID", "", 10);

// --- FUNCTION PROTOTYPES ---
// Notice the default arguments (= "") are placed HERE!
void updateScreen(String line1, String line2 = "", String line3 = "");
void drawLoadingAnim(String headerText);
void startLoading(String text);
void stopLoading();
void setupWiFi();
//void handleScreenSaver();
void performServerHealthCheck();
void sendTagEvent(String uid, String eventType);
String uidToString(uint8_t *uid, uint8_t length);
bool initializeNfc();
bool waitForPn5180Busy(uint8_t expectedLevel, unsigned long timeoutMs);
void printPn5180Version(const char *label, uint8_t address);
void recoverNfcRf();
// ---------------------------

void forceSaveToFlash() {
  Serial.println("FORCE SAVE TRIGGERED! Writing to flash...");
  
  String newUrl = custom_server_url.getValue();
  String newId = custom_sensor_id.getValue();

  Preferences preferences;
  preferences.begin("appData", false); 
  preferences.putString("serverUrl", newUrl);
  preferences.putString("sensorId", newId);
  preferences.end();
  
  Serial.println("Permanently locked in: " + newUrl);
}

// Catch BOTH types of saves!
void saveConfigCallback() { forceSaveToFlash(); }
void saveParamsCallback() { forceSaveToFlash(); }

void configModeCallback(WiFiManager *myWiFiManager)
{
  Serial.println("Entered config mode");
  digitalWrite(LED_PIN, HIGH);
  updateScreen("WiFi Setup Mode", "Connect to Wifi:", myWiFiManager->getConfigPortalSSID());
}

void setup()
{
  //handleScreenSaver();
  setCpuFrequencyMhz(80);
  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  pinMode(OLED_PWR, OUTPUT);
  digitalWrite(OLED_PWR, HIGH);
  delay(100);

  Wire.begin(OLED_SDA, OLED_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C))
  {
    Serial.println(F("SSD1306 allocation failed"));
    for (;;)
      ;
  }

  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  // Spins the animation for 1 second (4 frames * 250ms)
  for (int i = 0; i < 4; i++)
  {
    drawLoadingAnim("Booting System...");
    delay(250);
  }
  setupWiFi();
  performServerHealthCheck(); // <-- Called right here!

  nfcReady = initializeNfc();

  if (nfcReady) {
    updateScreen("System Ready", "Waiting for Tag...");
  } else {
    updateScreen("NFC ERROR", "Check PN5180 wiring", "See Serial Monitor");
  }
}

void loop()
{
  //handleScreenSaver();
  // --- SVELTE DASHBOARD HEARTBEAT ---
  if (isWifiConnected)
  {
    unsigned long currentMillis = millis();
    if (currentMillis - previousPingMillis >= pingInterval)
    {
      previousPingMillis = currentMillis;

      String pingUrl = serverUrl;
      pingUrl.replace("tag_event", "dispositivos/ping");

      HTTPClient http;
      http.begin(pingUrl);
      http.setTimeout(2000);
      http.addHeader("Content-Type", "application/json");
      String jsonPayload = "{\"dispositivo_id\": " + sensorId + "}";
      http.POST(jsonPayload);
      http.end();
    }
  }

  // --- NFC SCANNING LOGIC ---
  if (!nfcReady)
  {
    delay(1000);
    return;
  }

  uint8_t uid[10];
  uint8_t uidLength = nfc.readCardSerial(uid);

  if (uidLength > 0 && uid[0] != 0x00)
  {
    missCount = 0;
    idleMissCount = 0;

    if (!tagPresent)
    {
      tagPresent = true;
      currentUidLength = uidLength;
      lastPresentLogMillis = millis();

      for (int i = 0; i < uidLength; i++)
        currentUid[i] = uid[i];
      String uidStr = uidToString(currentUid, currentUidLength);

      // --- THE ADMIN TAG RESET INTERCEPTOR ---
      if (uidStr == ADMIN_TAG_UID)
      {
        Serial.println("ADMIN TAG DETECTED! Wiping Config...");
        updateScreen("ADMIN TAG", "Resetting Device...");
        digitalWrite(LED_PIN, HIGH);
        delay(2000);

        WiFiManager wm;
        wm.resetSettings();
        ESP.restart();
      }
      else
      {
        Serial.println("\n>>> TAG ARRIVED! UID: " + uidStr);
        sendTagEvent(uidStr, "ARRIVED");
      }
    }
    else
    {
      String uidStr = uidToString(uid, uidLength);
      String previousUidStr = uidToString(currentUid, currentUidLength);

      if (uidStr != previousUidStr)
      {
        Serial.println("\n>>> TAG CHANGED! OLD: " + previousUidStr + " NEW: " + uidStr);

        if (previousUidStr != ADMIN_TAG_UID)
        {
          sendTagEvent(previousUidStr, "REMOVED");
        }

        currentUidLength = uidLength;
        for (int i = 0; i < uidLength; i++)
          currentUid[i] = uid[i];

        if (uidStr != ADMIN_TAG_UID)
        {
          sendTagEvent(uidStr, "ARRIVED");
        }

        lastPresentLogMillis = millis();
      }
      else if (millis() - lastPresentLogMillis >= presentLogInterval)
      {
        lastPresentLogMillis = millis();
        Serial.println("TAG STILL PRESENT: " + uidStr);
      }
    }
  }
  else
  {
    if (tagPresent)
    {
      missCount++;
      if (missCount >= tagRemovedMissLimit)
      {
        String uidStr = uidToString(currentUid, currentUidLength);

        if (uidStr != ADMIN_TAG_UID)
        {
          sendTagEvent(uidStr, "REMOVED");
        }

        tagPresent = false;
        currentUidLength = 0;
        missCount = 0;
        recoverNfcRf();

        delay(1000);
        updateScreen("System Ready", "Waiting for Tag...");
      }
    }
    else
    {
      idleMissCount++;
      if (idleMissCount >= nfcRecoveryMissLimit)
      {
        idleMissCount = 0;
        recoverNfcRf();
      }
    }
  }
  delay(50);
}
