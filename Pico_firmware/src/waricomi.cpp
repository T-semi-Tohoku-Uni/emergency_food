#include <Arduino.h>
#include <PioEncoder.h>

// エンコーダーのA相ピンを指定（例: GPIO 2）
// ※B相は自動的に次のピン（GPIO 3）が割り当てられます。必ず連番のピンに接続してください。
PioEncoder myEnc(2);

long oldPosition = -999;

void setup() {
  Serial.begin(115200);
  
  // エンコーダー（PIOステートマシン）の動作を開始
  myEnc.begin();
  
  Serial.println("PIO Encoder Test Started:");
}

void loop() {
  // 現在のカウント値を取得
  long newPosition = myEnc.getCount();
  
  // 値に変化があった場合のみシリアルに出力
  if (newPosition != oldPosition) {
    oldPosition = newPosition;
    Serial.println(newPosition);
  }
}