import time
import os
import argparse
from controllers.i2c_controller import ServoController
from controllers.omni_controller import OmniSpeed
from controllers.serial_controller import SerialController
from controllers.arm_controller import ArmController
from controllers.line_detector import detect_line
from controllers.serial_calibrator import SerialCalibrator
from controllers.line_tracer import LineTracer
# from controllers.moveto import MoveOmni
from setup_logger import logger

def main():
    parser = argparse.ArgumentParser(description="ロボットのメインプログラム")
    parser.add_argument('--force-calibrate', action='store_true', help='保存されたデータがあっても強制的にキャリブレーションを実行する')
    args = parser.parse_args()

    logger.info("セットアップを行います")

    # シリアル通信の初期化 (環境に合わせてポート名を変更してください。例: Windowsなら 'COM3', Linuxなら '/dev/ttyACM0')
    serial_port = '/dev/ttyACM0' 
    baud_rate = 115200

    ball_area = [(0,0),(0,1),(1,0),(1,1),(2,0),(2,1),(3,0),(3,1)]
    area_step=0

    serial_ctrl = SerialController(port=serial_port, baud_rate=baud_rate)
    if not serial_ctrl.is_open():
        return
    
    servo_ctrl=ServoController()

    # オムニとアームの初期化 (開いたシリアル通信を渡す)
    omni = OmniSpeed(serial_instance=serial_ctrl.ser)
    arm = ArmController()
    #mov = MoveOmni()

    arm.set_position(140,50)

    processed_frame, cx, cy, is_cross, angle_diff = detect_line(crop=(0, 240, 1200, 240))

    CHANNELS = [1, 14, 15, 0]
    COMMANDS = ["vela", "velb", "velc", "veld"]

    calib_file = "calibration_data.json"

    # 保存済みのキャリブレーションデータが存在する場合は読み込む
    if os.path.exists(calib_file) and not args.force_calibrate:
        logger.info(f"保存されたキャリブレーションデータ ({calib_file}) を読み込みます。")
        omni.rot_servo.load_calibration(calib_file)
    else:
        # --- キャリブレーションの実行 ---
        if args.force_calibrate:
            logger.info("強制キャリブレーションが指定されました。自動キャリブレーションを開始します...")
        else:
            logger.info("キャリブレーションデータが見つからないため、自動キャリブレーションを開始します...")
        calibrator = SerialCalibrator(servo_ctrl=omni.rot_servo, serial_instance=serial_ctrl.ser)
        
        calibrator.calibrate_neutral_all(CHANNELS, COMMANDS, tolerance=0.5)
        logger.info("ニュートラル調整が完了しました。")

        final_scales_fw, final_scales_bw = calibrator.calibrate_speed_all(
            channels=CHANNELS, command_signals=COMMANDS, test_speed=0.5, target_velocity=30.0
        )
        logger.info(f"速度スケール -> 正転: {final_scales_fw}, 逆転: {final_scales_bw}")

        # 最後に再調整して結果を保存
        calibrator.calibrate_neutral_all(channels=CHANNELS, command_signals=COMMANDS, tolerance=0.5)
        
        omni.rot_servo.save_calibration(calib_file)
        logger.info("キャリブレーション結果を保存しました。次回からはスキップされます。")

    logger.info("セットアップが完了しました。'start robot!' の受信を待機します（Ctrl+Cで終了）")
    
    try:
        # "start robot!" を検知するまで待機するループ
        while True:
            # 受信バッファを確認してデータを取得
            received_data = serial_ctrl.check_incoming() 
            
            if received_data and "start robot!" in received_data:
                logger.info("'start robot!' を検知しました。ロボットのメイン動作を開始します！")
                break # 待機ループを抜けてメイン処理へ進む
                
            time.sleep(0.5) # 待機中のCPU負荷を下げるためのウェイト

        omni.Movexy(100,0)
        # "start robot!" 検知後のメインループ
        # ライントレース処理を実行
        
        # 速度を少しだけ落とし、急ハンドル（D項の暴走）を防ぐために kd を下げる
        tracer = LineTracer(omni=omni, serial_ctrl=serial_ctrl, base_speed=0.7, kp=0.0006, ki=0.0, kd=0.0024, debug=True)

        # 交差点を見つけるまでライントレースを実行するのを3回繰り返す
        for i in range(3):
            tracer.run(cross = True)
            tracer.run(timeout=0.3)


        
        omni.Movexy(ball_area[area_step][0]*150,ball_area[area_step][1]*400)

        


    except KeyboardInterrupt:
        logger.info("プログラムを終了します。")
    finally:
        serial_ctrl.close()


def search_in_ballarea():
    pass


if __name__ == "__main__":
    main()