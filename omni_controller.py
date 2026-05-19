import time
from i2c_controller import ServoController

# 方針
# その場回転とベクトルとxy方向の速度指定のコードを実装する。

class OmuniSpeed:
    def __init__(self,front_left=0,front_right=1,rear_left=2,rear_right=3):
        #speedxy用の変数
        self.front_left= front_left
        self.front_right = front_right
        self.rear_left = rear_left
        self.rear_right = rear_right

    def Speedxy(self,x,y):


    def SpeedPolar(self,x,y):
