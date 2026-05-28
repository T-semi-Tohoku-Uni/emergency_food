#ifndef LED_BLINKER_H
#define LED_BLINKER_H

#include <Arduino.h>

class LedBlinker {
private:
  uint8_t pin;       // LEDが接続されているピン番号
  bool ledState;     // LEDの現在の状態

public:
  // コンストラクタ（宣言のみ）
  LedBlinker(uint8_t ledPin);

  // 初期設定（宣言のみ）
  void begin();

  // LEDの状態を反転させる（宣言のみ）
  void toggle();
};

#endif // LED_BLINKER_H
