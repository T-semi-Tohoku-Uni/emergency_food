import time
from i2c_controller import ServoController
import math

# 方針
# その場回転とベクトルとxy方向の速度指定のコードを実装する。

class OmuniSpeed:
    def __init__(self,front_left=0,front_right=1,rear_left=2,rear_right=3):
        #speedxy用の変数
        self.front_left= front_left
        self.front_right = front_right
        self.rear_left = rear_left
        self.rear_right = rear_right
        # サーボコントローラーの初期化
        rot_servo = ServoController()

        # 前方をy,右向きをxと億
    def Speedxy(self,x,y):
        norm = 0.7
        nx = norm*x
        ny = norm*y

        v_a = nx - ny
        v_b = nx + ny
        v_c = -nx + ny
        v_d = -nx - ny
        
        rot_servo.set_speed(self.front_left, v_a)
        rot_servo.set_speed(self.front_right, v_b)
        rot_servo.set_speed(self.rear_left, v_c)
        rot_servo.set_speed(self.rear_right, v_d)        


    #前方向からの角度をphiとおく、
    def SpeedPolar(self,v,phi):
        root2^-1 = 0.707
        nx = v * root2^-1 * math.sin(math.radians(phi))
        ny = v * root2^-1 * math.cos(math.radians(phi))

        v_a = nx - ny
        v_b = nx + ny
        v_c = -nx + ny
        v_d = -nx - ny
        
        rot_servo.set_speed(self.front_left, v_a)
        rot_servo.set_speed(self.front_right, v_b)
        rot_servo.set_speed(self.rear_left, v_c)
        rot_servo.set_speed(self.rear_right, v_d) 

    def rotation(self,omega):
        norm = 1
        v_a = norm * omega
        v_b = norm * omega
        v_c = norm * omega
        v_d = norm * omega

        rot_servo.set_speed(self.front_left, v_a)
        rot_servo.set_speed(self.front_right, v_b)
        rot_servo.set_speed(self.rear_left, v_c)
        rot_servo.set_speed(self.rear_right, v_d) 