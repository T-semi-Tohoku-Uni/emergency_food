# i2c_controller.py
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

class ServoController:
    def __init__(self, channels=16):
        # I2Cバスの初期化
        self.i2c = busio.I2C(SCL, SDA)
        
        # PCA9685の初期化（デフォルトのI2Cアドレスは0x40）
        self.pca = PCA9685(self.i2c)
        
        # サーボモーターの標準的な周波数は50Hz
        self.pca.frequency = 50
        
        # 連続回転サーボの停止点（ニュートラル）オフセットを保持する辞書 (単位: マイクロ秒)
        self.calibration_offsets = {i: 0 for i in range(channels)}

        # サーボオブジェクトを格納するリスト
        self.servos = []
        for i in range(channels):
            # 一般的なSG90などのサーボはパルス幅 0.5ms(500us) ~ 2.4ms(2400us) で0〜180度動く
            # デフォルトでは標準サーボとして初期化しておく
            s = servo.Servo(self.pca.channels[i], min_pulse=500, max_pulse=2400)
            self.servos.append(s)

    def set_calibration_offset(self, channel, offset_us):
        """
        ローテーションサーボの停止点（ニュートラル位置）のずれをマイクロ秒単位で補正する
        channel: 0 ~ 15
        offset_us: ずらす量（例: 停止点が1520usなら +20 を指定）
        """
        self.calibration_offsets[channel] = offset_us
        # 既にContinuousServoとして初期化されている場合は、新しいオフセットで再設定
        if isinstance(self.servos[channel], servo.ContinuousServo):
            self.servos[channel] = servo.ContinuousServo(
                self.pca.channels[channel], min_pulse=700 + offset_us, max_pulse=2300 + offset_us
            )

    def set_angle(self, channel, angle):
        """
        指定したチャンネルのサーボを特定の角度に動かす
        channel: 0 ~ 15 (PCA9685のピン番号)
        angle: 0 ~ 180 (度)
        """
        # すでにローテーションサーボとして使われているチャンネルの誤操作を防ぐ
        if isinstance(self.servos[channel], servo.ContinuousServo):
            print(f"Error: チャンネル{channel}はローテーションサーボとして設定されています。")
            return

        if 0 <= angle <= 180:
            self.servos[channel].angle = angle
        else:
            print(f"Error: 角度は0から180の間で指定してください (入力値: {angle})")

    def set_speed(self, channel, speed):
        """
        指定したチャンネルのローテーション(連続回転)サーボの速度を設定する
        channel: 0 ~ 15
        speed: -1.0 (逆転最大) ~ 1.0 (正転最大), 0.0 で停止
        """
        # 初回呼び出し時に標準サーボオブジェクトをContinuousServoに置き換える
        if not isinstance(self.servos[channel], servo.ContinuousServo):
            offset = self.calibration_offsets[channel]
            self.servos[channel] = servo.ContinuousServo(
                self.pca.channels[channel], min_pulse=700 + offset, max_pulse=2300 + offset
            )

        # 速度を設定 (throttleプロパティを使用)
        if -1.0 <= speed <= 1.0:
            self.servos[channel].throttle = speed
        else:
            print(f"Error: 速度は-1.0から1.0の間で指定してください (入力値: {speed})")

    def cleanup(self):
        """終了時にPCA9685の出力をリセットする"""
        self.pca.deinit()