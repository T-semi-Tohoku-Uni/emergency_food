#include <Arduino.h>
#include <Encoder.h> // 追加: 信頼性の高い標準ライブラリ

// Encoderライブラリは内部で割り込みと状態遷移を使用して
// 機械式エンコーダーのチャタリング（ノイズ）を自動的に防ぎます
Encoder myEncoder1(2, 3);
Encoder myEncoder2(4, 5);

long lastStep1 = 0;
long lastStep2 = 0;
unsigned long lastTime = 0;

void setup() {
  Serial.begin(115200);
  lastTime = millis();
}

void loop() {
  unsigned long currentTime = millis();
  float dt = (currentTime - lastTime) / 1000.0;

  // 100ミリ秒ごとに計算して出力 (delayを使わない非同期処理)
  if (dt >= 0.1) {
    long currentStep1 = myEncoder1.read();
    long currentStep2 = myEncoder2.read();

    float vel1 = (currentStep1 - lastStep1) / dt;
    float vel2 = (currentStep2 - lastStep2) / dt;

    Serial.print("Encoder1 - Step: ");
    Serial.print(currentStep1);
    Serial.print(", Vel: ");
    Serial.print(vel1); 

    Serial.print(" | Encoder2 - Step: ");
    Serial.print(currentStep2);
    Serial.print(", Vel: ");
    Serial.println(vel2); 

    lastStep1 = currentStep1;
    lastStep2 = currentStep2;
    lastTime = currentTime;
  }
}