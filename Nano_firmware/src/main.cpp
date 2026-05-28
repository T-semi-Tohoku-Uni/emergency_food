#include <Arduino.h>
#include "ReadEncoder.h"


// Raspberry Pi PicoはほぼすべてのGPIOピンで外部割り込み(attachInterrupt)が可能です。
// 複数のエンコーダーを簡単に接続できます。
ReadEncoder myEncoder1(2, 3); // 1つ目のエンコーダー (GP2, GP3)
ReadEncoder myEncoder2(4, 5); // 2つ目のエンコーダー (GP4, GP5)

// 1つ目のエンコーダー用ISR
void encoder1ISR() {
  myEncoder1.handleInterrupt();
}

// 2つ目のエンコーダー用ISR
void encoder2ISR() {
  myEncoder2.handleInterrupt();
}

void setup() {
  Serial.begin(115200);
  
  myEncoder1.begin();
  myEncoder2.begin();

  // それぞれのAピン(2番, 4番)の立下り(FALLING)エッジで割り込みを発生させる
  attachInterrupt(digitalPinToInterrupt(2), encoder1ISR, FALLING);
  attachInterrupt(digitalPinToInterrupt(4), encoder2ISR, FALLING);
}

void loop() {
  // エンコーダー1のステップ数と回転速度
  Serial.print("Encoder1 - Step: ");
  Serial.print(myEncoder1.getStep());
  Serial.print(", Vel: ");
  Serial.print(myEncoder1.getVelocity()); 

  // エンコーダー2のステップ数と回転速度
  Serial.print(" | Encoder2 - Step: ");
  Serial.print(myEncoder2.getStep());
  Serial.print(", Vel: ");
  Serial.println(myEncoder2.getVelocity()); 


  delay(100); // 100ミリ秒待機
}