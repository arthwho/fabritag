String uidToString(uint8_t *uid, uint8_t length) {
  String s = "";
  for (int i = 0; i < length; i++) {
    if (uid[i] < 0x10) s += "0";
    s += String(uid[i], HEX);
  }
  s.toUpperCase();
  return s;
}

bool waitForPn5180Busy(uint8_t expectedLevel, unsigned long timeoutMs) {
  unsigned long start = millis();

  while (digitalRead(PN5180_BUSY) != expectedLevel) {
    if (millis() - start >= timeoutMs) {
      return false;
    }
    delay(1);
  }

  return true;
}

void printPn5180Version(const char *label, uint8_t address) {
  uint8_t version[2] = {0x00, 0x00};

  nfc.readEEprom(address, version, sizeof(version));

  Serial.print(label);
  Serial.print(": 0x");
  if (version[0] < 0x10) Serial.print("0");
  Serial.print(version[0], HEX);
  Serial.print(" 0x");
  if (version[1] < 0x10) Serial.print("0");
  Serial.println(version[1], HEX);
}

bool initializeNfc() {
  Serial.println();
  Serial.println("--- PN5180 DIAGNOSTICO ---");
  Serial.println("Controle: NSS/CS=5, BUSY=22, RST=21");
  Serial.println("SPI ESP32 VSPI esperado: SCK=18, MISO=19, MOSI=23");

  updateScreen("Starting NFC...", "PN5180 init...");

  nfc.begin();
  SPI.begin(PN5180_SCK, PN5180_MISO, PN5180_MOSI, PN5180_NSS);

  // Keep BUSY from floating if the module/cable is disconnected.
  pinMode(PN5180_BUSY, INPUT_PULLUP);

  if (!waitForPn5180Busy(LOW, 500)) {
    Serial.println("ERRO: BUSY nao ficou LOW. Confira 3V3, GND e fio BUSY no GPIO 22.");
    return false;
  }

  Serial.println("1. Reset PN5180...");
  nfc.reset();

  Serial.println("2. Lendo EEPROM de versao...");
  printPn5180Version("Product version", PRODUCT_VERSION);
  printPn5180Version("Firmware version", FIRMWARE_VERSION);
  printPn5180Version("EEPROM version", EEPROM_VERSION);

  Serial.println("3. Configurando RF ISO14443A...");
  if (!nfc.setupRF()) {
    Serial.println("ERRO: setupRF() falhou.");
    return false;
  }

  Serial.println("--- NFC INICIADO COM SUCESSO ---");
  return true;
}

void recoverNfcRf() {
  Serial.println("Recovering PN5180 RF field...");

  nfc.reset();

  if (!nfc.setupRF()) {
    Serial.println("ERRO: PN5180 RF recovery failed.");
    nfcReady = false;
    updateScreen("NFC ERROR", "RF recovery failed", "Restart device");
    return;
  }

  Serial.println("PN5180 RF field recovered.");
}
