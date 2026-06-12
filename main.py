import time
from controllers.i2c_controller import ServoController
from controllers.omni_controller import OmniSpeed
from controllers.serial_controller import SerialController
from controllers.arm_controller import ArmController
from controllers.line_detector import detect_line
from controllers.serial_calibrator import SerialCalibrator
from controllers.line_tracer import LineTracer
from setup_logger import logger

def main():
    logger.info("セットアップを行います")

    # シリアル通信の初期化 (環境に合わせてポート名を変更してください。例: Windowsなら 'COM3', Linuxなら '/dev/ttyACM0')
    serial_port = '/dev/ttyACM0' 
    baud_rate = 115200

    serial_ctrl = SerialController(port=serial_port, baud_rate=baud_rate)
    if not serial_ctrl.is_open():
        return

    # オムニとアームの初期化 (開いたシリアル通信を渡す)
    omni = OmniSpeed(serial_instance=serial_ctrl.ser)
    arm = ArmController()

    processed_frame, cx, cy, is_cross = detect_line(crop=(0, 240, 3280, 240))

    # --- キャリブレーションの実行（完全停止の調整） ---
    logger.info("サーボモーターのニュートラル（完全停止点）キャリブレーションを開始します...")
    calibrator = SerialCalibrator(servo_ctrl=omni.rot_servo, serial_instance=serial_ctrl.ser)
    
    channels = [omni.front_right, omni.front_left, omni.rear_left, omni.rear_right]
    commands = ["vela", "velb", "velc", "veld"]
    
    # 全輪の停止点を自動調整 (Pico側のエンコーダー速度を読み取って停止点を探します)
    calibrator.calibrate_neutral_all(channels, commands, tolerance=0.5)
    logger.info("キャリブレーションが完了し、完全停止のオフセットが設定されました。")

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

        # "start robot!" 検知後のメインループ
        # ライントレース処理を実行
        tracer = LineTracer(omni=omni, serial_ctrl=serial_ctrl, base_speed=0.3, kp=0.0005, ki=0.0, kd=0.0)
        # 10秒間だけライントレースを実行し、その後自動で停止する
        tracer.run(timeout=10.0)

    except KeyboardInterrupt:
        logger.info("プログラムを終了します。")
    finally:
        serial_ctrl.close()

if __name__ == "__main__":
    main()