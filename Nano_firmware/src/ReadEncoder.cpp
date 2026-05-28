#include "LedBlinker.h"

// コンストラクタの実装
LedBlinker::LedBlinker(uint8_t ledPin) {
  pin = ledPin;
  ledState = false;
}

// beginメソッドの実装
void LedBlinker::begin() {
  pinMode(pin, OUTPUT);
}

// toggleメソッドの実装
void LedBlinker::toggle() {
  ledState = !ledState;
  digitalWrite(pin, ledState);
}
