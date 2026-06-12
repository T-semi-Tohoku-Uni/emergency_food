import time
from controllers.i2c_controller import ServoController
import math

# 方針
# アームの伸ばしたい位置と高さをコードで指定する。
# 単位はmm
# arm_length_1はハンドに近いほう、arm_length_2は根元に近いほう
# 限界値はエラーを出すようにする。

class ArmController:
    def __init__(self,right_servo=7,left_servo=8,arm_length_1=80,arm_length_2=80,min_angle=0,max_angle=170):
        #channel名の設定
        self.right_servo = right_servo
        self.left_servo = left_servo

        # アームの長さの定義
        self.arm_length_1 = arm_length_1
        self.arm_length_2 = arm_length_2

        # サーボコントローラーの初期化
        self.servo_ctrl = ServoController(max_angle=180)

        # アームの限界値の定義（ここにまとめるのがベストです）
        self._max_height = 90
        self._min_height = 0
        self._max_length = 180
        self._min_length = 30
        self._drive_base = 30

        self.max_angle = max_angle
        self.min_angle = min_angle
        # 【追加】初期化の最後に、安全な待機姿勢（ホームポジション）に移動させる
        # 例：前方に100mm、高さ50mmの位置で待機
        self.set_position(100, 50)

    def set_position(self, length, height):
        # アームの長さと高さを指定して動かす

        # アームの位置が限界を超えていないかを確認
        self._check_limits(length, height)
        
        alfa = math.atan2(height,length)
        radius = math.sqrt(length**2 + height**2)

        # 逆運動学の計算式を実装する
        angle_right_servo = alfa + math.acos((length**2 + height**2 + self.arm_length_1**2 - self.arm_length_2**2) / (2 * self.arm_length_1 * radius))
        angle_left_servo  = alfa + math.asin((length**2 + height**2 - self.arm_length_1**2 + self.arm_length_2**2) / (2 * self.arm_length_2 * radius))

        # 現状のコードだと絶対にservoの角度が限界以上回そうとしてしまうはずなので、
        # そうならないように改良する必要がある。

        # 角度を度数法に変換する
        deg_right = math.degrees(angle_right_servo) + 45
        deg_left  = math.degrees(angle_left_servo) + 45

        # 左サーボの回転方向が反対のため、180度から引いて反転させる
        deg_right = 180.0 - deg_right

        print(f"計算されたサーボの角度 -> 右: {deg_right:.1f}度, 左: {deg_left:.1f}度")

        # サーボの限界値以内かチェックする
        deg_right = self._check_angle(deg_right)
        deg_left  = self._check_angle(deg_left)

        self._check_diff_angle(deg_right, deg_left)
        
        self.servo_ctrl.set_angle(self.right_servo, deg_right)
        self.servo_ctrl.set_angle(self.left_servo, deg_left)

    def _check_limits(self, length, height):
        # 1. 指定されたXY座標が設定した矩形エリア内に収まっているかチェック
        if not (self._min_length <= length <= self._max_length and 
                self._min_height <= height <= self._max_height and 
                self._drive_base <= length + height):
            raise ValueError(f"エラー: 指定された位置(長さ:{length}mm, 高さ:{height}mm)はXY限界値を超えています！")
            
        # 2. 【追加】アームの物理的な最大リーチ（到達可能距離）のチェック
        radius = math.sqrt(length**2 + height**2)
        max_reach = self.arm_length_1 + self.arm_length_2
        
        if radius > max_reach:
            raise ValueError(f"エラー: 目標地点への直線距離({radius:.1f}mm)が、アームの最大リーチ({max_reach}mm)を超えており物理的に届きません！")
            
        return True
    
    def _check_angle(self, angle):
        # サーボの角度が 0〜120度の範囲内か確認する
        if self.min_angle <= angle <= self.max_angle:
            return angle
        else:
            raise ValueError(f"エラー: 計算されたサーボの角度({angle:.1f}度)が可動範囲({self.min_angle}〜{self.max_angle}度)を超えています！")
    
    def _check_diff_angle(self, angle1, angle2):
        # 2つのサーボの角度差がmax_diff度以内か確認する
        max_diff = 270-30
        if abs(angle1 + angle2) <= max_diff:
            return True
        else:
            raise ValueError(f"エラー: サーボ間の角度差({abs(angle1 + angle2):.1f}度)が{max_diff}度を超えています！")
