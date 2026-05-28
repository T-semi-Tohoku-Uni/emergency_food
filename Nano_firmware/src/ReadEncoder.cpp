#include "ReadEncoder.h"

// コンストラクタの実装
ReadEncoder::ReadEncoder(uint8_t cone_pinA, uint8_t cone_pinB) {
  pinA = cone_pinA;
  pinB = cone_pinB; // セミコロンを追加
  encoderStep = 0;  // カウントを0で初期化
  lastStep = 0;
  lastTime = 0;
}

// beginメソッドの実装
void ReadEncoder::begin() {
  pinMode(pinA, INPUT_PULLUP);
  pinMode(pinB, INPUT_PULLUP);
  lastTime = millis();            // 現在の時間を記録
}

// 割り込み処理（AピンのFALLINGで呼び出される）
void ReadEncoder::handleInterrupt() {
  // 呼ばれた時はすでにAピンがLOWに変化しているので、Bピンの状態だけで方向を判定できる
  if (digitalRead(pinB) == HIGH) {
    encoderStep++; // 時計回り
  } else {
    encoderStep--; // 反時計回り
  }
}

// 現在のステップ数を返すメソッドの実装
long ReadEncoder::getStep() {
  // 8bitマイコンではlong(4byte)の読み取り中に割り込まれるとデータが壊れるため、
  // 一時的に割り込みを停止して安全に値をコピーする
  noInterrupts();
  long currentStep = encoderStep;
  interrupts();
  return currentStep;
}

// 回転速度（ステップ数/秒）を計算して返す
float ReadEncoder::getVelocity() {
  unsigned long currentTime = millis();
  long currentStep = getStep();
  
  float dt = (currentTime - lastTime) / 1000.0; // 経過時間（秒）
  if (dt <= 0.0) return 0.0; // ゼロ除算防止

  float velocity = (currentStep - lastStep) / dt;
  
  // 次回の計算のために更新
  lastStep = currentStep;
  lastTime = currentTime;
  
  return velocity;
}
