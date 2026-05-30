#include <Arduino.h>
//#include <PioEncoder.h> // 変更: PIOを利用したエンコーダーライブラリ
#include <pio_encoder.h>

// エンコーダーのインスタンスを作成
// (PioEncoderは連続した2つのピンを使用するため、最初のピン番号のみを指定します)
PioEncoder myEncoder_a(21); // ピン2と3を使用
PioEncoder myEncoder_b(9); // ピン4と5を使用
PioEncoder myEncoder_c(13); // ピン6と7を使用
PioEncoder myEncoder_d(17); // ピン8と9を使用

long lastStep_a = 0;
long lastStep_b = 0;
long lastStep_c = 0;
long lastStep_d = 0;
unsigned long lastTime = 0;

void setup() {
  Serial.begin(115200);
  
  // PIOエンコーダーの初期化
  myEncoder_a.begin();
  myEncoder_b.begin();
  myEncoder_c.begin();
  myEncoder_d.begin();
  
  Serial.println("PIO Encoder Test Started:");
  lastTime = millis();
}

void loop() {
  unsigned long currentTime = millis();
  // unsigned long型同士の引き算により、オーバーフロー発生時も正しい経過時間が計算されます
  unsigned long elapsedTime = currentTime - lastTime;

  // 小数誤差を避けるため、経過時間をマイクロ秒（100,000us = 100ms）のまま判定
  if (elapsedTime >= 100) {
    // 実際の経過時間を元に dt を計算し、速度の計算精度を保つ
    float dt = elapsedTime / 100.0; 
    // 変更: PIOステートマシンから現在のカウントを取得
    long currentStep_a = myEncoder_a.getCount();
    long currentStep_b = myEncoder_b.getCount();
    long currentStep_c = myEncoder_c.getCount();
    long currentStep_d = myEncoder_d.getCount();

    float vel_a = (currentStep_a - lastStep_a) / dt;
    float vel_b = (currentStep_b - lastStep_b) / dt;
    float vel_c = (currentStep_c - lastStep_c) / dt;
    float vel_d = (currentStep_d - lastStep_d) / dt;

    //Serial.print("a - Step: ");
    //Serial.print(currentStep_a);
    Serial.print(", Vel_a: ");
    Serial.print(vel_a); 

    //Serial.print(" | b - Step: ");
    //Serial.print(currentStep_b);
    Serial.print(", Vel_b: ");
    Serial.print(vel_b); 

    //Serial.print(" | c - Step: ");
    //Serial.print(currentStep_c);
    Serial.print(", Vel_c: ");
    Serial.print(vel_c); 

    //Serial.print(" | d - Step: ");
    //Serial.print(currentStep_d);
    Serial.print(", Vel_d: ");
    Serial.println(vel_d); 

    lastStep_a = currentStep_a;
    lastStep_b = currentStep_b;
    lastStep_c = currentStep_c;
    lastStep_d = currentStep_d;

    // 速度計算のブレを防ぐため、実際の計測時刻で lastTime を更新する
    lastTime = currentTime;
  }
}