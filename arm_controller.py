import time
from i2c_controller import ServoController
import math

# 方針
# アームの伸ばしたい位置と高さをコードで指定する。
# 単位はmm
# arm_length_1はハンドに近いほう、arm_length_2は根元に近いほう
# 限界値はエラーを出すようにする。

class ArmController:
    def __init__(self,right_servo=7,left_servo=8,arm_length_1=80,arm_length_2=80,max_angle=1.0):
        #channel名の設定
        self.right_servo = right_servo
        self.left_servo = left_servo

        # アームの長さの定義
        self.arm_length_1 = arm_length_1
        self.arm_length_2 = arm_length_2

        # サーボコントローラーの初期化
        self.servo_ctrl = ServoController()

        # アームの限界値の定義（ここにまとめるのがベストです）
        self._max_height = 90
        self._min_height = 0
        self._max_length = 150
        self._min_length = 30
        self._drive_base = 30

        # モーターの最大許容速度を定義
        self.max_angle = max_angle

    def set_position(self, length, height):
        # アームの長さと高さを指定して動かす
        self._check_limits(length, height)
        
        alfa = math.atan2(height,length)
        radius = math.sqrt(length**2 + height**2)

        # 逆運動学の計算式を実装する
        # 注意: Pythonでは2乗の計算に ^ ではなく ** を使用します
        angle_right_servo = alfa + math.acos((length**2 + height**2 + self.arm_length_1**2 - self.arm_length_2**2) / (2 * self.arm_length_1 * radius))
        angle_left_servo  = alfa + math.asin((length**2 + height**2 - self.arm_length_1**2 + self.arm_length_2**2) / (2 * self.arm_length_2 * radius))

        self.servo_ctrl.set_angle(self.right_servo, math.degrees(angle_right_servo))
        self.servo_ctrl.set_angle(self.left_servo, math.degrees(angle_left_servo))



    def _check_limits(self, length, height):
        # アームの先端のハンドの位置が限界値を超えていないかチェックする
        if self._min_length <= length <= self._max_length and self._min_height <= height <= self._max_height and self._drive_base <= length+height:
            return True
        else:
            # 限界値を超えている場合はエラーを発生させて強制停止する
            raise ValueError(f"エラー: 指定された位置(長さ:{length}mm, 高さ:{height}mm)は物理的な限界値を超えています！")
    
    def _check_angle(self,angle):
        pass
