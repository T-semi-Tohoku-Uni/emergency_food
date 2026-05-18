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
        
        # サーボオブジェクトを格納するリスト
        self.servos = []
        for i in range(channels):
            # 一般的なSG90などのサーボはパルス幅 0.5ms(500us) ~ 2.4ms(2400us) で0〜180度動く
            # お使いのサーボに合わせて min_pulse / max_pulse は調整してください
            s = servo.Servo(self.pca.channels[i], min_pulse=500, max_pulse=2400)
            self.servos.append(s)

    def set_angle(self, channel, angle):
        """
        指定したチャンネルのサーボを特定の角度に動かす
        channel: 0 ~ 15 (PCA9685のピン番号)
        angle: 0 ~ 180 (度)
        """
        if 0 <= angle <= 180:
            self.servos[channel].angle = angle
        else:
            print(f"Error: 角度は0から180の間で指定してください (入力値: {angle})")

    def cleanup(self):
        """終了時にPCA9685の出力をリセットする"""
        self.pca.deinit()