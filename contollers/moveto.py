import time
from contollers.i2c_controller import ServoController
import math
from contollers.omni_controller import OmniSpeed

class MoveOmnu():
    def __init__(self, wheel_size = 42, pulses_per_revolution = 24*4):
        
        # クラスの初期化
        self.rot_servo = ServoController()
        self.omni = OmniSpeed()

        self.wheel_size = 42
        self.pulses_per_revolution = pulses_per_revolution

    def movexy(self, x, y, speed=0.5):
        # 前方をx、右向きをyとする
        wheel_rotation_x = x / self.wheel_size
        wheel_rotation_y = y / self.wheel_size

        self.omni.Speedxy




        




    
    def movepolar(self, r, theta):
        # 前方をr,時計回りにthetaとする