#include "ReadEncoder.h"

// コンストラクタの実装
ReadEncoder::ReadEncoder(uint8_t cone_pinA, uint8_t cone_pinB) {
  pinA = cone_pinA;
  pinB = cone_pinB; // セミコロンを追加
  encoderStep = 0;  // カウントを0で初期化
}

// beginメソッドの実装
void ReadEncoder::begin() {
  pinMode(pinA, INPUT_PULLUP);
  pinMode(pinB, INPUT_PULLUP);
  lastStateA = digitalRead(pinA); // 初期状態を記録
  lastStateB = digitalRead(pinB); // 初期状態を記録
}

// エンコーダーの読み取り処理
void ReadEncoder::ReadState() {
  uint8_t currentStateA = digitalRead(pinA);

  // Aピンの状態が変わった時（パルスの立ち下がり）に処理を行う
  if (currentStateA != lastStateA && currentStateA == LOW) {
    // その時のBピンの状態で回転方向を判定する
    if (digitalRead(pinB) == HIGH) {
      encoderStep++; // 時計回り
    } else {
      encoderStep--; // 反時計回り
    }
  }
  lastStateA = currentStateA; // 今回の状態を保存
}

// 現在のステップ数を返すメソッドの実装
long ReadEncoder::getStep() {
  return encoderStep;
}
