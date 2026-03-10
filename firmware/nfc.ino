String uidToString(uint8_t *uid, uint8_t length) {
  String s = "";
  for (int i = 0; i < length; i++) {
    if (uid[i] < 0x10) s += "0";
    s += String(uid[i], HEX);
  }
  s.toUpperCase();
  return s;
}