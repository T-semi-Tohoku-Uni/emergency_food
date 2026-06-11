import time
import sys
import os
# パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from controllers.i2c_controller import ServoController
import math
import serial

# 方針
# その場回転とベクトルとxy方向の速度指定のコードを実装する。

class OmniSpeed:
    def __init__(self,front_right=1,front_left=14,rear_left=15,rear_right=0,max_speed = 1.0, wheel_size = 42, pulses_per_revolution = 24*4):
        #speedxy用の変数
        self.front_right = front_right
        self.front_left= front_left
        self.rear_left = rear_left
        self.rear_right = rear_right
        # サーボコントローラーの初期化
        self.rot_servo = ServoController()

        ## 1/√2の計算
        self.inv_root2 = 1.0 / math.sqrt(2)

        # モーターの最大許容速度を定義
        self.max_speed = max_speed

        self.wheel_size = 42
        self.pulses_per_revolution = pulses_per_revolution

        self.commands = ["stepa","stepb","stepc","stepd"]

        self.SERIAL_PORT = "/dev/ttyACM0"
        self.BAUDRATE = 115200

        self.serial = serial.Serial(self.SERIAL_PORT, self.BAUDRATE, timeout=1.0)
        time.sleep(2) # シリアル接続の確立待ち
    
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
        
        # サーボの入力範囲(-1.0 ~ 1.0)に正規化
        v_a /= self.max_speed
        v_b /= self.max_speed
        v_c /= self.max_speed
        v_d /= self.max_speed
        
        self.rot_servo.set_speed(self.front_right, v_a)
        self.rot_servo.set_speed(self.front_left, v_b)
        self.rot_servo.set_speed(self.rear_left, v_c)
        self.rot_servo.set_speed(self.rear_right, v_d)

        # 前方をy,右向きをxと置く
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

    def Speedxy_rotation(self, x, y, omega):
        nx = self.inv_root2 * x
        ny = self.inv_root2 * y
        # 平行移動の成分と、回転の成分(omega)を足し合わせる
        v_a = nx - ny + omega
        v_b = nx + ny + omega
        v_c = -nx + ny + omega
        v_d = -nx - ny + omega

        self._set_motors(v_a, v_b, v_c, v_d)

    def Movexy(self, x, y, speed=0.5):
        # 前方をx、右向きをyとする
        wheel_rotation_x = x / self.wheel_size * self.inv_root2 * self.pulses_per_revolution
        wheel_rotation_y = y / self.wheel_size * self.inv_root2 * self.pulses_per_revolution
        wheel_rotation = math.sqrt(wheel_rotation_x**2 + wheel_rotation_y**2)

        pulses = [0,0,0,0]

        pulses[0] =  wheel_rotation_x - wheel_rotation_y
        pulses[1] =  wheel_rotation_x + wheel_rotation_y
        pulses[2] = -wheel_rotation_x + wheel_rotation_y
        pulses[3] = -wheel_rotation_x - wheel_rotation_y

        nom = []

        for i in range(4):
            nom.append(self.normalize(pulses[i],speed))
        
        self.serial.write(("stepinit" + '\n').encode('utf-8'))

        line = [0,0,0,0]
        trigger = [0,0,0,0]
        while True:
            self._set_motors(nom[0],nom[1],nom[2],nom[3])
            for i in range(4):
                self.serial.write((self.commands[i] + '\n').encode('utf-8'))

                # 送り返されたパルス数を受信（エラー処理を追加）
                raw_data = self.serial.readline().decode('utf-8').strip()
                try:
                    line[i] = float(raw_data)
                except ValueError:
                    continue # 受信失敗時は前回の値を維持してループを続行

                # 目標パルスまでの誤差
                error = math.fabs(pulses[i] - line[i])
                if error < 50:
                    nom[i] = nom[i] / 2.0
            
                # 逆回転時(負の値)にも正しく判定できるように絶対値を取る。または誤差が少ない場合
                if math.fabs(nom[i]) < 0.1 or error < 10:
                    trigger[i] = 1
                    nom[i] = 0.0 # 完了した車輪の速度を0にする
            
            if sum(trigger) == 4:
                break
        
        # 最後に全てのモーターを完全に停止させる
        self._set_motors(0.0, 0.0, 0.0, 0.0)

    def normalize(self, n, r):
        if n == 0:
            return 0.0
        if math.fabs(n) > 1:
            re = n/math.fabs(n)*r
        else:
            re = n*r
        return re