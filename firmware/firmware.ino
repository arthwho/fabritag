#include <PN5180.h>
#include <PN5180ISO14443.h>
#include <WiFi.h>
#include <HTTPClient.h>

// --- CONFIGURAÇÃO ---
const char *ssid = "ssid";
const char *password = "password";
const char *serverUrl = "http://192.168.2.XX:5000/api/tag_event"; // IP do seu PC
const int sensorId = 1;                                           // Registrado na tabela SENSOR do PostgreSQL

// Definições de pinos do PN5180
#define PN5180_NSS 5
#define PN5180_BUSY 22
#define PN5180_RST 21

// Instancia o leitor ISO14443
PN5180ISO14443 nfc(PN5180_NSS, PN5180_BUSY, PN5180_RST);

// Variáveis de controle de estado
bool tagPresent = false;
uint8_t currentUid[10];
uint8_t currentUidLength = 0;
int missCount = 0;
int dotCounter = 0;

void setupWiFi()
{
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected.");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void sendTagEvent(String uid, String event)
{
  if (WiFi.status() == WL_CONNECTED)
  {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    String jsonPayload = "{\"epc_tag\": \"" + uid + "\", \"sensor_id\": " + String(sensorId) + ", \"event\": \"" + event + "\", \"rssi\": 0}";

    Serial.print("Sending event: ");
    Serial.println(jsonPayload);

    int httpResponseCode = http.POST(jsonPayload);

    if (httpResponseCode > 0)
    {
      String response = http.getString();
      Serial.println("Server Response: " + response);
    }
    else
    {
      Serial.print("Error on sending POST: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  }
  else
  {
    Serial.println("WiFi Disconnected. Cannot send event.");
  }
}

String uidToString(uint8_t *uid, uint8_t len)
{
  String s = "";
  for (int i = 0; i < len; i++)
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
  delay(1000);

  setupWiFi();

  Serial.println("==================================");
  Serial.println("PN5180 MIFARE PostgreSQL Client");
  Serial.println("==================================");

  nfc.begin();
  nfc.reset();
  nfc.setupRF();

  Serial.println("Initialization complete. Bring your MIFARE tag near...");
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
      sendTagEvent(uidStr, "ARRIVED");
    }
    else
    {
      Serial.print("h"); // mantendo
    }
  }
  else
  {
    if (tagPresent)
    {
      missCount++;
      if (missCount >= 3)
      {
        String uidStr = uidToString(currentUid, currentUidLength);
        Serial.println("\n<<< TAG REMOVED! UID: " + uidStr);
        sendTagEvent(uidStr, "REMOVED");

        tagPresent = false;
        currentUidLength = 0;
      }
    }
    else
    {
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
