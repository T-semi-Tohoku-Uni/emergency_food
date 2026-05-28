#ifndef READ_ENCODER_H
#define READ_ENCODER_H

#include <Arduino.h>

class ReadEncoder {
private:
  uint8_t pinA;       // エンコーダーのAピン
  uint8_t pinB;      // エンコーダーのBピン
  volatile long encoderStep; // 割り込みで値が変わるため volatile を付与

  long lastStep;          // 速度計算用：前回のステップ数
  unsigned long lastTime; // 速度計算用：前回の時間（ミリ秒）

public:
  // コンストラクタ
  ReadEncoder(uint8_t cone_pinA, uint8_t cone_pinB);

  // 初期設定
  void begin();

  // 割り込み発生時に呼び出すメソッド
  void handleInterrupt();

  // 現在のカウントや回転速度を取得する
  long getStep();
  float getVelocity();
};

#endif // READ_ENCODER_H
