#include <Arduino.h>
//#include <PioEncoder.h> // 変更: PIOを利用したエンコーダーライブラリ
#include <pio_encoder.h>

// エンコーダーのインスタンスを作成
// (PioEncoderは連続した2つのピンを使用するため、最初のピン番号のみを指定します)
PioEncoder myEncoder1(9); // ピン2と3を使用
PioEncoder myEncoder2(13); // ピン4と5を使用

long lastStep1 = 0;
long lastStep2 = 0;
unsigned long lastTime = 0;

void setup() {
  Serial.begin(115200);
  
  // PIOエンコーダーの初期化
  myEncoder1.begin();
  myEncoder2.begin();

  lastTime = millis();
}

void loop() {
  unsigned long currentTime = millis();
  float dt = (currentTime - lastTime) / 1000.0;

  // 100ミリ秒ごとに計算して出力 (delayを使わない非同期処理)
  if (dt >= 0.1) {
    // 変更: PIOステートマシンから現在のカウントを取得
    long currentStep1 = myEncoder1.getCount();
    long currentStep2 = myEncoder2.getCount();

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