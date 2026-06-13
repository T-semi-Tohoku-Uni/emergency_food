#include <Arduino.h>
//#include <PioEncoder.h> // 変更: PIOを利用したエンコーダーライブラリ
#include <pio_encoder.h>

// LEDのピン番号定義
const uint8_t LED1_PIN = 6;
const uint8_t LED2_PIN = 7;
const uint8_t LED3_PIN = 8;

// ボタンのピン番号定義
const uint8_t BUTTON_PIN = 20;

// エンコーダーのインスタンスを作成
// (PioEncoderは連続した2つのピンを使用するため、最初のピン番号のみを指定します)
PioEncoder myEncoder_a(21); // ピン21と22を使用
PioEncoder myEncoder_b(9); // ピン9と10を使用
PioEncoder myEncoder_c(13); // ピン13と14を使用
PioEncoder myEncoder_d(17); // ピン17と18を使用

long lastStep_a = 0;
long lastStep_b = 0;
long lastStep_c = 0;
long lastStep_d = 0;
unsigned long lastTime = 0;
bool led1State = false;
bool led2State = false;
bool led3State = false;

// 最新のエンコーダー値と速度を保持する変数
long current_step_a = 0;
long current_step_b = 0;
long current_step_c = 0;
long current_step_d = 0;
float current_vel_a = 0.0;
float current_vel_b = 0.0;
float current_vel_c = 0.0;
float current_vel_d = 0.0;

// エンコーダーのステップ数をリセットするためのオフセット変数
long offset_a = 0;
long offset_b = 0;
long offset_c = 0;
long offset_d = 0;

// ボタンのチャタリング対策用変数
bool buttonState = HIGH;
bool lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;

void setup() {
  Serial.begin(115200);
  
  // PIOエンコーダーの初期化
  myEncoder_a.begin();
  myEncoder_b.begin();
  myEncoder_c.begin();
  myEncoder_d.begin();
  
  // LEDピンを出力に設定
  pinMode(LED1_PIN, OUTPUT);
  pinMode(LED2_PIN, OUTPUT);
  pinMode(LED3_PIN, OUTPUT);

  // ボタンピンを入力（内部プルアップ有効）に設定
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  Serial.println("PIO Encoder Test Started:");
  lastTime = millis();
}

void loop() {
  unsigned long currentTime = millis();

  // ボタンの状態読み取り（チャタリング対策付き）
  bool reading = digitalRead(BUTTON_PIN);
  if (reading != lastButtonState) {
    lastDebounceTime = currentTime;
  }
  if ((currentTime - lastDebounceTime) > 30) { // 50msのデバウンス時間
    if (reading != buttonState) {
      buttonState = reading;
      if (buttonState == LOW) { // プルアップ設定のため、LOWが「押された」状態
        Serial.println("start robot!");
      }
    }
  }
  lastButtonState = reading;
  // シリアル通信から特定の指令が来たとき返答する
  if (Serial.available() > 0) {
    // 改行コード（Enter）が来るまで文字列としてまとめて読み込む
    String cmd = Serial.readStringUntil('\n'); 
    
    // Windows環境などから送られる見えない改行コード(\r)や空白を取り除く
    cmd.trim(); 

    // シリアル通信から特定の指令が来たとき返答する
    if (cmd == "led1on") {
      led1State = true;
      digitalWrite(LED1_PIN, led1State);
      Serial.println("LED 1 turned on");
    } else if (cmd == "led1off") {
      led1State = false;
      digitalWrite(LED1_PIN, led1State);
      Serial.println("LED 1 turned off");
    } else if(cmd == "led2on") {
      led2State = true;
      digitalWrite(LED2_PIN, led2State);
      Serial.println("LED 2 turned on");
    } else if (cmd == "led2off") {
      led2State = false;
      digitalWrite(LED2_PIN, led2State);
      Serial.println("LED 2 turned off");
    } else if(cmd == "led3on") {
      led3State = true;
      digitalWrite(LED3_PIN, led3State);
      Serial.println("LED 3 turned on");
    } else if (cmd == "led3off") {
      led3State = false;
      digitalWrite(LED3_PIN, led3State);
      Serial.println("LED 3 turned off");
    } else if (cmd == "initstep") {
      offset_a = current_step_a;
      offset_b = current_step_b;
      offset_c = current_step_c;
      offset_d = current_step_d;
      Serial.println("Encoder steps reset");
    } else if (cmd == "stepa") {
      Serial.println(current_step_a - offset_a); 
    } else if (cmd == "stepb") {
      Serial.println(current_step_b - offset_b);
    } else if (cmd == "stepc") {
      Serial.println(current_step_c - offset_c);
    } else if (cmd == "stepd") {
      Serial.println(current_step_d - offset_d);
    } else if (cmd == "vela") {
      Serial.println(current_vel_a);
    } else if (cmd == "velb") {
      Serial.println(current_vel_b);
    } else if (cmd == "velc") {
      Serial.println(current_vel_c);
    } else if (cmd == "veld") {
      Serial.println(current_vel_d);
    } else if (cmd == "stepall"){
      Serial.print(current_step_a - offset_a); 
      Serial.print(",");
      Serial.print(current_step_b - offset_b); 
      Serial.print(",");
      Serial.print(current_step_c - offset_c); 
      Serial.print(",");
      Serial.println(current_step_d - offset_d); 
    }
  }

  // unsigned long型同士の引き算により、オーバーフロー発生時も正しい経過時間が計算されます
  unsigned long elapsedTime = currentTime - lastTime;

  // 小数誤差を避けるため、経過時間をマイクロ秒（100,000us = 100ms）のまま判定
  if (elapsedTime >= 100) {
    // 実際の経過時間を元に dt を計算し、速度の計算精度を保つ
    float dt = elapsedTime / 100.0; 
    // 変更: PIOステートマシンから現在のカウントを取得
    current_step_a = myEncoder_a.getCount();
    current_step_b = myEncoder_b.getCount();
    current_step_c = myEncoder_c.getCount();
    current_step_d = myEncoder_d.getCount();

    current_vel_a = (current_step_a - lastStep_a) / dt;
    current_vel_b = (current_step_b - lastStep_b) / dt;
    current_vel_c = (current_step_c - lastStep_c) / dt;
    current_vel_d = (current_step_d - lastStep_d) / dt;

    lastStep_a = current_step_a;
    lastStep_b = current_step_b;
    lastStep_c = current_step_c;
    lastStep_d = current_step_d;

    // 速度計算のブレを防ぐため、実際の計測時刻で lastTime を更新する
    lastTime = currentTime;
  }
}