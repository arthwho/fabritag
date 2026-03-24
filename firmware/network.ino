void setupWiFi() {
  Preferences preferences;
  preferences.begin("appData", true); 
  serverUrl = preferences.getString("serverUrl", "http://192.168.2.174:5000/api/tag_event"); 
  sensorId = preferences.getString("sensorId", "1");
  preferences.end();

  WiFiManager wm;
  
  std::vector<const char *> menu = {"wifi", "info", "param", "sep", "restart", "exit"};
  wm.setMenu(menu);

  wm.setSaveConfigCallback(saveConfigCallback);
  wm.setSaveParamsCallback(saveParamsCallback); // <-- ADD THIS LINE!
  wm.setAPCallback(configModeCallback);
  wm.setClass("invert"); 
  wm.setTitle("Fabritag Manager");
  wm.setCustomHeadElement(customPortalCSS);

  custom_server_url.setValue(serverUrl.c_str(), 60);
  custom_sensor_id.setValue(sensorId.c_str(), 10);

  wm.addParameter(&custom_server_url);
  wm.addParameter(&custom_sensor_id);

  startLoading("Connecting WiFi...");
  
  bool connected = wm.autoConnect("Fabritag-Setup");
  
  stopLoading();

  if (!connected) {
    Serial.println("Failed to connect and hit timeout");
    updateScreen("WiFi Error!", "Rebooting...");
    delay(3000);
    ESP.restart();
  }

  isWifiConnected = true;
  digitalWrite(LED_PIN, LOW); 
  Serial.println("\nWiFi connected.");
  updateScreen("WiFi Connected!", WiFi.localIP().toString());
  delay(1500); 
}

void performServerHealthCheck() {
  startLoading("Checking Server...");
  
  String statusUrl = serverUrl;
  statusUrl.replace("tag_event", "status"); 
  
  HTTPClient http;
  http.begin(statusUrl);
  http.setTimeout(5000); 
  int httpCode = http.GET();
  http.end();
  
  stopLoading();
  
  if (httpCode <= 0 || httpCode == 404) {
    Serial.println("Server health check failed! IP might be wrong.");
    updateScreen("Server Not Found!", "Opening Setup Portal");
    digitalWrite(LED_PIN, HIGH); 
    delay(2000);
    
    WiFiManager wm;
    std::vector<const char *> menu = {"wifi", "info", "param", "sep", "restart", "exit"};
    wm.setMenu(menu);
    wm.setSaveConfigCallback(saveConfigCallback);
    wm.setSaveParamsCallback(saveParamsCallback); // <-- ADD THIS LINE!
    wm.setClass("invert"); 
    wm.setTitle("Fabritag Manager");
    wm.setCustomHeadElement(customPortalCSS);
    
    // Re-attach the global parameters so you can edit the wrong IP!
    wm.addParameter(&custom_server_url);
    wm.addParameter(&custom_sensor_id);
    
    // Open the portal on demand
    if (!wm.startConfigPortal("Fabritag-Setup")) {
      Serial.println("Portal timeout, rebooting...");
      delay(3000);
      ESP.restart();
    }
    
    // If you fix the IP and hit save, store it and reboot!
    if (shouldSaveConfig) {
      serverUrl = custom_server_url.getValue();
      sensorId = custom_sensor_id.getValue();
      
      Preferences preferences;
      preferences.begin("appData", false); 
      preferences.putString("serverUrl", serverUrl);
      preferences.putString("sensorId", sensorId);
      preferences.end();
    }
    ESP.restart(); 
  } else {
    Serial.println("Server is online and responding!");
    updateScreen("Server Online!", "Ready.");
    delay(1000);
  }
}
// ------------------------------------

void sendTagEvent(String uid, String eventType) {
  if (isWifiConnected) {
    updateScreen("Tag: " + uid, "Event: " + eventType, "Syncing DB...");
    digitalWrite(LED_PIN, HIGH); 
    
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    String jsonPayload = "{\"epc_tag\": \"" + uid + "\", \"sensor_id\": " + sensorId + ", \"event\": \"" + eventType + "\", \"rssi\": 0}";
    
    int httpResponseCode = http.POST(jsonPayload);
    
    if (httpResponseCode > 0) {
      updateScreen("Tag: " + uid, "Event: " + eventType, "DB Sync: SUCCESS");
    } else {
      updateScreen("Tag: " + uid, "Event: " + eventType, "DB Sync: FAILED");
    }
    http.end();
    digitalWrite(LED_PIN, LOW); 
  }
}