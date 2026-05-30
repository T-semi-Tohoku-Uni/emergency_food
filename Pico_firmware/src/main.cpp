#include <Arduino.h>
#include <RotaryEncoder.h> // 変更: Pico対応のライブラリ

// エンコーダーのインスタンスを作成
RotaryEncoder myEncoder1(2, 3);
RotaryEncoder myEncoder2(4, 5);

// ----------------------------------------------------
// 割り込み時に実行される関数 (Interrupt Service Routines)
// ----------------------------------------------------
// ピンの電圧が変化した瞬間にこれが呼ばれ、カウントを取りこぼさず更新します
void checkPosition1() {
  myEncoder1.tick();
}

void checkPosition2() {
  myEncoder2.tick();
}
// ----------------------------------------------------

long lastStep1 = 0;
long lastStep2 = 0;
unsigned long lastTime = 0;

void setup() {
  Serial.begin(115200);
  
  // Picoのピンに割り込み（Interrupt）を設定
  // ピン2, 3, 4, 5 のどれかが変化(CHANGE)したら、対応する関数を瞬時に呼び出す
  attachInterrupt(digitalPinToInterrupt(2), checkPosition1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(3), checkPosition1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(4), checkPosition2, CHANGE);
  attachInterrupt(digitalPinToInterrupt(5), checkPosition2, CHANGE);

  lastTime = millis();
}

void loop() {
  unsigned long currentTime = millis();
  float dt = (currentTime - lastTime) / 1000.0;

  // 100ミリ秒ごとに計算して出力 (delayを使わない非同期処理)
  if (dt >= 0.1) {
    // 変更: read() ではなく getPosition() を使用して現在のステップ数を取得
    long currentStep1 = myEncoder1.getPosition();
    long currentStep2 = myEncoder2.getPosition();

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