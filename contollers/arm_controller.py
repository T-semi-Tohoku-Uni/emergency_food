import time
from contollers.i2c_controller import ServoController
import math

# 方針
# アームの伸ばした長さと高さをコードで指定する。
# 限界値はエラーを出すようにする。

###
class OmniSpeed:
    def __init__(self,front_left=0,front_right=1,rear_left=2,rear_right=3,max_speed = 1.0):
        #speedxy用の変数
        self.front_left= front_left
        self.front_right = front_right
        self.rear_left = rear_left
        self.rear_right = rear_right
        # サーボコントローラーの初期化
        self.rot_servo = ServoController()

        ## 1/√2の計算
        self.inv_root2 = 1.0 / math.sqrt(2)

        # モーターの最大許容速度を定義
        self.max_speed = max_speed
    
    # モーターへの出力処理を1つのメソッドに共通化
    def _set_motors(self, v_a, v_b, v_c, v_d):
        # 4つの車輪の速度のうち、絶対値の最大値を求める
        max_val = max(abs(v_a), abs(v_b), abs(v_c), abs(v_d))
        
        # 最大値が設定した最大速度を超えている場合、比率を保って全体を縮小
        if max_val > self.max_speed:
            scale = self.max_speed / max_val
            v_a *= scale
            v_b *= scale
            v_c *= scale
            v_d *= scale
        
        self.rot_servo.set_speed(self.front_left, v_a)
        self.rot_servo.set_speed(self.front_right, v_b)
        self.rot_servo.set_speed(self.rear_left, v_c)
        self.rot_servo.set_speed(self.rear_right, v_d)

        # 前方をy,右向きをxと億
    def Speedxy(self,x,y):
        nx = self.inv_root2 * x
        ny = self.inv_root2 * y

        v_a = nx - ny
        v_b = nx + ny
        v_c = -nx + ny
        v_d = -nx - ny
        
        self._set_motors(v_a, v_b, v_c, v_d)       


    #前方向からの角度をphiとおく、
    def SpeedPolar(self,v,phi):
        rad = math.radians(phi)
        nx = v * self.inv_root2 * math.sin(rad)
        ny = v * self.inv_root2 * math.cos(rad)

        v_a = nx - ny
        v_b = nx + ny
        v_c = -nx + ny
        v_d = -nx - ny
        
        self._set_motors(v_a, v_b, v_c, v_d)
    
    def rotation(self,omega):
        v_a = omega
        v_b = omega
        v_c = omega
        v_d = omega

        self._set_motors(v_a, v_b, v_c, v_d) 
###