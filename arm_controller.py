import time
from i2c_controller import ServoController
import math

# 方針
# アームの伸ばした長さと高さをコードで指定する。
# 限界値はエラーを出すようにする。

class ArmController:
    def __init__(self,right_servo=7,left_servo=8,max_speed=1.0):
        #channel名の設定
        self.right_servo = right_servo
        self.left_servo = left_servo

        # サーボコントローラーの初期化
        self.servo_ctrl = ServoController()

        # モーターの最大許容速度を定義
        self.max_speed = max_speed

    def set_position(self, length, height):
        """アームの長さと高さを指定して動かす（公開メソッドの例）"""
        self._check_limits(length, height)
        pass

    def _check_limits(self, length, height):
        """限界値を超えていないかチェックする（非公開メソッドの例）"""
        pass