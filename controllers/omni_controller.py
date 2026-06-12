import time
import sys
import os
# パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from controllers.i2c_controller import ServoController
import math
import serial
from setup_logger import logger

# 方針
# その場回転とベクトルとxy方向の速度指定のコードを実装する。

class OmniSpeed:
    def __init__(self, servo_ctrl=None, front_right=1,front_left=14,rear_left=15,rear_right=0,max_speed = 1.0, wheel_size = 42, pulses_per_revolution = 24*4, serial_instance=None):
        #speedxy用の変数
        self.front_right = front_right
        self.front_left= front_left
        self.rear_left = rear_left
        self.rear_right = rear_right
        # サーボコントローラーの初期化
        if servo_ctrl:
            self.rot_servo = servo_ctrl
        else:
            self.rot_servo = ServoController()
        
        # モーターの滑らかな加減速（スルーレート制限）用の変数
        self.current_speeds = [0.0, 0.0, 0.0, 0.0]
        self.max_accel = 0.05  # 1回の更新で許容する最大変化量（小さいほど滑らかになる）

        ## 1/√2の計算
        self.inv_root2 = 1.0 / math.sqrt(2)

        # モーターの最大許容速度を定義
        self.max_speed = max_speed

        self.wheel_size = 42
        self.pulses_per_revolution = pulses_per_revolution

        self.commands = ["stepa","stepb","stepc","stepd"]

        self.SERIAL_PORT = "/dev/ttyACM0"
        self.BAUDRATE = 115200

        if serial_instance is not None:
            self.serial = serial_instance
        else:
            self.serial = serial.Serial(self.SERIAL_PORT, self.BAUDRATE, timeout=1.0)
            time.sleep(2) # シリアル接続の確立待ち
        logger.info("OmniSpeedの初期化が完了しました。")
    
    # モーターへの出力処理を1つのメソッドに共通化
    def _set_motors(self, v_a, v_b, v_c, v_d, smooth=False):
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
        targets = [
            v_a / self.max_speed,
            v_b / self.max_speed,
            v_c / self.max_speed,
            v_d / self.max_speed
        ]
        
        # 滑らかな加減速処理（スルーレート制限）
        if smooth:
            for i in range(4):
                diff = targets[i] - self.current_speeds[i]
                if diff > self.max_accel:
                    targets[i] = self.current_speeds[i] + self.max_accel
                elif diff < -self.max_accel:
                    targets[i] = self.current_speeds[i] - self.max_accel
                    
        # 現在の速度として記録
        self.current_speeds = list(targets)
        
        self.rot_servo.set_speed(self.front_right, self.current_speeds[0])
        self.rot_servo.set_speed(self.front_left, self.current_speeds[1])
        self.rot_servo.set_speed(self.rear_left, self.current_speeds[2])
        self.rot_servo.set_speed(self.rear_right, self.current_speeds[3])

        # 前方をy,右向きをxと置く
    def Speedxy(self, x, y, smooth=True):
        nx = self.inv_root2 * x
        ny = self.inv_root2 * y

        v_a = nx - ny
        v_b = nx + ny
        v_c = -nx + ny
        v_d = -nx - ny
        
        self._set_motors(v_a, v_b, v_c, v_d, smooth=smooth)       


    #前方向からの角度をphiとおく、
    def SpeedPolar(self, v, phi, smooth=True):
        rad = math.radians(phi)
        nx = v * self.inv_root2 * math.sin(rad)
        ny = v * self.inv_root2 * math.cos(rad)

        v_a = nx - ny
        v_b = nx + ny
        v_c = -nx + ny
        v_d = -nx - ny
        
        self._set_motors(v_a, v_b, v_c, v_d, smooth=smooth)
    
    def rotation(self, omega, smooth=True):
        v_a = omega
        v_b = omega
        v_c = omega
        v_d = omega

        self._set_motors(v_a, v_b, v_c, v_d, smooth=smooth) 

    def Speedxy_rotation(self, x, y, omega, smooth=True):
        nx = self.inv_root2 * x
        ny = self.inv_root2 * y
        # 平行移動の成分と、回転の成分(omega)を足し合わせる
        v_a = nx - ny + omega
        v_b = nx + ny + omega
        v_c = -nx + ny + omega
        v_d = -nx - ny + omega

        self._set_motors(v_a, v_b, v_c, v_d, smooth=smooth)

    def stop(self, calibrate=False):
        """
        全てのモーターを即座に停止させる
        calibrate=True の場合、その場でニュートラルキャリブレーションを実行し、完全に静止させます。
        """
        self._set_motors(0.0, 0.0, 0.0, 0.0, smooth=False)
        
        if calibrate:
            from controllers.serial_calibrator import SerialCalibrator
            calibrator = SerialCalibrator(servo_ctrl=self.rot_servo, serial_instance=self.serial)
            channels = [self.front_right, self.front_left, self.rear_left, self.rear_right]
            calibrator.calibrate_neutral_all(channels, self.commands, tolerance=0.5)
        logger.info("全モーターを停止しました。")

    def Movexy(self, x, y, speed=0.5):
        logger.info(f"指定距離移動を開始: x={x}, y={y}, speed={speed}")
        
        # 前方をx、右向きをyとする
        wheel_rotation_x = x / self.wheel_size * self.inv_root2 * self.pulses_per_revolution
        wheel_rotation_y = y / self.wheel_size * self.inv_root2 * self.pulses_per_revolution

        pulses = [0,0,0,0]

        pulses[0] = -wheel_rotation_x + wheel_rotation_y
        pulses[1] =  wheel_rotation_x + wheel_rotation_y
        pulses[2] =  wheel_rotation_x - wheel_rotation_y
        pulses[3] = -wheel_rotation_x - wheel_rotation_y

        # 各車輪の基準となる速度（比率を維持した最大速度）
        base_nom = [self.normalize(pulses[i], speed) for i in range(4)]
        
        self.serial.write(("initstep" + '\n').encode('utf-8'))

        line = [0,0,0,0]
        
        # 安全対策：永遠に走り続けるのを防ぐためのタイムアウト設定
        distance = math.sqrt(x**2 + y**2)
        timeout_seconds = (distance / 50.0) + 5.0 
        start_time = time.time()
        
        while True:
            # タイムアウトのチェック
            if (time.time() - start_time) > timeout_seconds:
                logger.warning(f"移動がタイムアウトしました。現在のエンコーダ値: {line}")
                break
            
            # 値の「ズレ」を防ぐため、送信する直前に古い受信データを捨てる
            self.serial.reset_input_buffer()
            
            # マイコンに4つのエンコーダ値をまとめて要求するコマンド（Pico側のプログラムに合わせて "stepall" などに変更してください）
            self.serial.write(("stepall" + '\n').encode('utf-8'))

            # マイコンが返答を準備する時間
            time.sleep(0.01)

            raw_data = self.serial.readline().decode('utf-8').strip()
            if raw_data:
                # カンマ区切りで受信した文字列を分割（スペース区切りの場合は raw_data.split() に変更してください）
                parts = raw_data.split(',')
                if len(parts) >= 4:
                    for i in range(4):
                        try:
                            line[i] = float(parts[i].strip())
                        except ValueError:
                            continue

            # 各車輪の目標までの残りパルス数を計算
            # （モーターの回転方向とエンコーダの正負が逆になっても無限ループしないよう、絶対値で比較します）
            remaining_pulses = []
            for i in range(4):
                if pulses[i] != 0:
                    rem = abs(pulses[i]) - abs(line[i])
                else:
                    rem = 0.0
                remaining_pulses.append(max(0.0, rem))
                
            max_remaining = max(remaining_pulses)

            # 全ての車輪が目標付近（残り10未満）に到達、または通り過ぎたら終了
            if max_remaining < 10:
                logger.info(f"移動完了: 目標={pulses}, 最終エンコーダ値={line}")
                break

            # P制御（比例制御）による減速: 残りパルスが指定値未満になったら徐々に減速
            decel_threshold = 100.0  # 減速を開始する残りパルス数（実機に合わせて調整してください）
            scale = 1.0
            if max_remaining < decel_threshold:
                scale = max(0.15, max_remaining / decel_threshold) # 最低速度(0.15)を確保して途中停止を防ぐ

            # 4輪の比率を保ったままモーターに出力
            current_nom = [base_nom[i] * scale for i in range(4)]
            self._set_motors(*current_nom)

            time.sleep(0.1)
        
        # 最後に全てのモーターを完全に停止させる
        self._set_motors(0.0, 0.0, 0.0, 0.0)
        logger.info("指定距離移動が完了しました。")

    def normalize(self, n, r):
        if n == 0:
            return 0.0
        if math.fabs(n) > 1:
            re = n/math.fabs(n)*r
        else:
            re = n*r
        return re
