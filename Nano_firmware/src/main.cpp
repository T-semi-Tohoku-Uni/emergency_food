#include <Arduino.h>

// LEDの現在の状態を覚えておくための変数
bool ledState = false; 

void setup() {
  Serial.begin(115200);
  
  // 内蔵LED（通常は13番ピン）を出力モードに設定
  pinMode(LED_BUILTIN, OUTPUT); 
}

void loop() {
  // 1. センサー値の読み取りと送信
  int sensor1 = analogRead(A0);
  int sensor2 = analogRead(A1);

  Serial.print(sensor1);
  Serial.print(",");
  Serial.println(sensor2); 

  // 2. Lチカ（通信インジケーター）
  ledState = !ledState;                  // 状態を反転させる（ONならOFF、OFFならONに）
  digitalWrite(LED_BUILTIN, ledState);   // LEDに状態を書き込む

  delay(100); // 100ミリ秒待機
}