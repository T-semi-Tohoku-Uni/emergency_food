import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from setup_logger import logger
from controllers.line_detector import detect_line

class LineTracer:
    def __init__(self, omni, serial_ctrl, base_speed=0.3, kp=0.0005, ki=0.0, kd=0.0):
        """
        ライントレースを実行するクラス
        omni: OmniSpeedインスタンス
        serial_ctrl: SerialControllerインスタンス
        base_speed: 前進する基本速度
        kp: 比例ゲイン（現在のズレに対する修正力）
        ki: 積分ゲイン（過去のズレの蓄積に対する修正力）
        kd: 微分ゲイン（ズレの変化量に対する修正力、振動を抑える）
        """
        self.omni = omni
        self.serial_ctrl = serial_ctrl
        self.base_speed = base_speed
        self.kp = kp
        self.ki = ki
        self.kd = kd
        
        # カメラの画像幅が 3280 のため、その中心である 1640 を基準にする
        self.center_x = 3280 // 2  

        # PID制御用の変数
        self.last_diff = 0.0
        self.integral = 0.0

    def run(self):
        logger.info("ライントレースを開始します！")
        
        while True:
            # シリアル通信からの終了信号（再度 "start robot!"）をチェック
            received_data = self.serial_ctrl.check_incoming()
            if received_data and "start robot!" in received_data:
                logger.info("再度 'start robot!' を検知しました。ライントレースを終了し、ロボットを停止します。")
                self.omni.Speedxy(0, 0)
                break

            # 画面の下半分を切り取って線を検知
            processed_frame, cx, cy = detect_line(crop=(0, 240, 3280, 240))
            
            if cx is not None:
                # 画像の中心からのズレを算出
                diff = cx - self.center_x
                
                # PID制御の計算
                self.integral += diff
                derivative = diff - self.last_diff
                omega = (diff * self.kp) + (self.integral * self.ki) + (derivative * self.kd)
                
                self.last_diff = diff
                
                self.omni.Speedxy_rotation(0, self.base_speed, omega)
            else:
                # 線が見つからない場合は安全のため停止
                self.integral = 0.0
                self.last_diff = 0.0
                self.omni.Speedxy(0, 0)
                
            time.sleep(0.05)