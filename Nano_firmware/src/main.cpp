#include <Arduino.h>
#include "ReadEncoder.h"


// インスタンスの作成。Arduino Nanoの外部割り込み対応ピンは 2番 と 3番 です。
ReadEncoder myEncoder(2, 3); 

// 割り込みサービスルーチン (ISR)
// attachInterruptにはクラスのメソッドを直接渡せないため、この関数でラップします。
void encoderISR() {
  myEncoder.handleInterrupt();
}

void setup() {
  Serial.begin(115200);
  
  myEncoder.begin();

  // 2番ピン（pinA）の立下り(FALLING)エッジで割り込みを発生させる
  attachInterrupt(digitalPinToInterrupt(2), encoderISR, FALLING);
}

void loop() {
  // 1. エンコーダーのステップ数と回転速度を計算して送信
  Serial.print("Step: ");
  Serial.print(myEncoder.getStep());
  Serial.print(", Velocity(step/s): ");
  Serial.println(myEncoder.getVelocity()); 


  delay(100); // 100ミリ秒待機
}