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

        pulses = [0,0,0,0]

        pulses[0] =  wheel_rotation_x - wheel_rotation_y
        pulses[1] =  wheel_rotation_x + wheel_rotation_y
        pulses[2] = -wheel_rotation_x + wheel_rotation_y
        pulses[3] = -wheel_rotation_x - wheel_rotation_y

        # 各車輪の基準となる速度（比率を維持した最大速度）
        base_nom = [self.normalize(pulses[i], speed) for i in range(4)]
        
        self.serial.write(("initstep" + '\n').encode('utf-8'))

        line = [0,0,0,0]
        while True:
            for i in range(4):
                # 1. 送信前に受信バッファに残っている古いデータを消去してズレを防ぐ
                self.serial.reset_input_buffer()
                
                # 2. コマンドを送信
                self.serial.write((self.commands[i] + '\n').encode('utf-8'))
                
                # 3. 少しだけ待つ（Pico側が確実に処理して返答を返すための余裕）
                time.sleep(0.01)

                # 4. 返答を受信
                raw_data = self.serial.readline().decode('utf-8').strip()
                
                # ★デバッグ: 実際に何を受け取っているかコンソールに表示
                # print(f"[{self.commands[i]}] 受信データ: '{raw_data}'")

                if not raw_data:
                    print(f"[警告] {self.commands[i]} の返答が空(タイムアウト)です")
                    continue

                # 送り返されたパルス数を受信（エラー処理を追加）
                #print(raw_data)
                try:
                    line[i] = float(raw_data)
                except ValueError:
                    continue # 受信失敗時は前回の値を維持してループを続行

            # 各車輪の目標までの残りパルス数を計算（オーバーシュート時は0とする）
            remaining_pulses = []
            for i in range(4):
                if pulses[i] > 0:
                    rem = pulses[i] - line[i]
                elif pulses[i] < 0:
                    rem = line[i] - pulses[i]
                else:
                    rem = 0.0
                remaining_pulses.append(max(0.0, rem))
                
            max_remaining = max(remaining_pulses)

            # 全ての車輪が目標付近（残り10未満）に到達、または通り過ぎたら終了
            if max_remaining < 10:
                break

            # P制御（比例制御）による減速: 残りパルスが指定値未満になったら徐々に減速
            decel_threshold = 100.0  # 減速を開始する残りパルス数（実機に合わせて調整してください）
            scale = 1.0
            if max_remaining < decel_threshold:
                scale = max(0.15, max_remaining / decel_threshold) # 最低速度(0.15)を確保して途中停止を防ぐ

            # 4輪の比率を保ったままモーターに出力
            current_nom = [base_nom[i] * scale for i in range(4)]
            self._set_motors(*current_nom)
        
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
