import time
import os
import argparse
import math
import cv2
from controllers.i2c_controller import ServoController
from controllers.omni_controller import OmniSpeed
from controllers.serial_controller import SerialController
from controllers.arm_controller import ArmController
from controllers.line_detector import detect_line
from controllers.serial_calibrator import SerialCalibrator
from controllers.line_tracer import LineTracer
# from controllers.moveto import MoveOmni
from setup_logger import logger
from controllers.ball_detector import BallDetector
from controllers.camera import Camera

def main():
    omni = OmniSpeed(servo_ctrl=servo_ctrl, serial_instance=serial_ctrl.ser)

    omni.Movexy(0,140)
    omni.Movexy(-200,0)

if __name__ == "__main__":
    main()