#ifndef READ_ENCODER_H
#define READ_ENCODER_H

#include <Arduino.h>

class ReadEncoder {
private:
  uint8_t pinA;       // エンコーダーのAピン
  uint8_t pinB;      // エンコーダーのBピン
  uint8_t EncoderStep;     // エンコーダーの状態

public:
  // コンストラクタ（宣言のみ）
  LedBlinker(uint8_t cone_pinA, uint8_t cone_pinB);

  // 初期設定（宣言のみ）
  void begin();

  // LEDの状態を反転させる（宣言のみ）
  void ReadState();
};

#endif // READ_ENCODER_H
