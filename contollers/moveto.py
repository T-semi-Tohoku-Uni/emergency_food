import time
import sys
import os
# パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

import math
from contollers.i2c_controller import ServoController
from contollers.omni_controller import OmniSpeed

class MoveOmni():
    def __init__(self, wheel_size = 42, pulses_per_revolution = 24*4):
        
        # クラスの初期化
        self.rot_servo = ServoController()
        self.omni = OmniSpeed()

        self.wheel_size = 42
        self.pulses_per_revolution = pulses_per_revolution

        self.inv_root2 = 1.0 / math.sqrt(2)

        self.SERIAL_PORT = "/dev/ttyACM0"
        self.BAUDRATE = 115200

        self.serial = serial.Serial(port, baudrate, timeout=1.0)
        time.sleep(2) # シリアル接続の確立待ち

    def movexy(self, x, y, speed=0.5):
        Serial = Ser(servo_ctrl, port=SERIAL_PORT, baudrate=BAUDRATE)

        # 前方をx、右向きをyとする
        wheel_rotation_x = x / self.wheel_size * self.inv_root2 * self.pulues_per_revolution
        wheel_rotation_y = y / self.wheel_size * self.inv_root2 * self.pulses_per_revolution

        pulues_a =  wheel_rotation_x - wheel_rotation_y
        pulues_b =  wheel_rotation_x + wheel_rotation_y
        pulues_c = -wheel_rotation_x - wheel_rotation_y
        pulues_d = -wheel_rotation_x - wheel_rotation_y
        
        self.omni.Speedxy(x,y)

        




        




    
    def movepolar(self, r, theta):
        # 前方をr,時計回りにthetaとする