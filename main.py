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
    
    # ServoControllerのインスタンスをここで1つだけ作成し、全体で共有する
    servo_ctrl = ServoController()

    # オムニとアームの初期化 (開いたシリアル通信を渡す)
    omni = OmniSpeed(servo_ctrl=servo_ctrl, serial_instance=serial_ctrl.ser)
    arm = ArmController(servo_ctrl=servo_ctrl)
    
    # カメラを初期化（最大解像度で1つだけ作成し、全体で共有する）
    # クロップを使わずに指定通りの解像度を引き出すため、標準的な16:9の比率を使用します
    cam = Camera(width=3280, height=180)
    detector = BallDetector(camera_instance=cam)

    arm.set_position(140,70)

    servo_ctrl.set_angle(9, 90)
    arm.set_position(60,100)

    # 最初のライントレース用の切り取りと検知
    test_frame = cam.capture()
    processed_frame, cx, cy, is_cross, angle_diff = detect_line(test_frame)

    CHANNELS = [1, 14, 15, 0]
    COMMANDS = ["vela", "velb", "velc", "veld"]

    calib_file = "calibration_data.json"

    # 保存済みのキャリブレーションデータが存在する場合は読み込む
    if os.path.exists(calib_file) and not args.force_calibrate:
        logger.info(f"保存されたキャリブレーションデータ ({calib_file}) を読み込みます。")
        servo_ctrl.load_calibration(calib_file)
        
        # 読み込んだオフセットを適用し、確実にモーターを静止状態(0.0)で初期化する
        for ch in CHANNELS:
            servo_ctrl.set_speed(ch, 0.0)
    else:
        # --- キャリブレーションの実行 ---
        if args.force_calibrate:
            logger.info("強制キャリブレーションが指定されました。自動キャリブレーションを開始します...")
        else:
            logger.info("キャリブレーションデータが見つからないため、自動キャリブレーションを開始します...")
        calibrator = SerialCalibrator(servo_ctrl=servo_ctrl, serial_instance=serial_ctrl.ser)
        
        calibrator.calibrate_neutral_all(CHANNELS, COMMANDS, tolerance=0.5)
        logger.info("ニュートラル調整が完了しました。")

        final_scales_fw, final_scales_bw = calibrator.calibrate_speed_all(
            channels=CHANNELS, command_signals=COMMANDS, test_speed=0.5, target_velocity=30.0
        )
        logger.info(f"速度スケール -> 正転: {final_scales_fw}, 逆転: {final_scales_bw}")

        # 最後に再調整して結果を保存
        calibrator.calibrate_neutral_all(channels=CHANNELS, command_signals=COMMANDS, tolerance=0.5)
        time.sleep(2)
        calibrator.calibrate_neutral_all(channels=CHANNELS, command_signals=COMMANDS, tolerance=0.5)
        
        servo_ctrl.save_calibration(calib_file)
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
        arm.set_position(140,70)
        servo_ctrl.set_angle(9, 60)

        logger.info(f"ラインを読める位置まで移動します")
        omni.Movexy(0,140)
        # "start robot!" 検知後のメインループ
        # ライントレース処理を実行
        
        # 速度を少しだけ落とし、急ハンドル（D項の暴走）を防ぐために kd を下げる
        # diffが相対値(-1.0 ~ 1.0)になったため、kpとkdの値を新しいスケールに合わせて調整
        tracer = LineTracer(omni=omni, serial_ctrl=serial_ctrl, camera=cam, base_speed=0.7, kp=0.7, ki=0.0, kd=1.5, debug=False)

        # 交差点を見つけるまでライントレースを実行するのを3回繰り返す
        for i in range(2):
            tracer.run(cross = True)
            logger.info(f"ラインを越えます")
            tracer.run(timeout=0.3)
        tracer.run(cross = True)
        logger.info(f"ライントレースが終了しました。")

        while True:
            
            logger.info(f"ボールエリアに移動")
            arm.set_position(100,100)

            omni.Movexy(ball_area[area_step//2][0]*150,ball_area[area_step//2][1]*400)
            
            logger.info(f"ボールの探索と、ボールを中心にとらえる処理を実行")
            # ボール探索用にカメラの解像度を広くし、エラーを防ぐためFPSを自動で落とす
            cam.set_resolution(3280, 2400)
            
            while True:
                ball_color = search_in_ballarea(omni, detector)
                if ball_color != None:
                    break
                omni.Movexy(0,50)
            
            area_step += 1
            arm.set_position(100,70)
            servo_ctrl.set_angle(9, 100)
            arm.set_position(100,100)

            omni.Movexy(ball_area[area_step//2][0]*70,0)
            omni.turn()
            tracer.run(timeout=3)

            if ball_color == "blue":
                logger.info(f"青色のボールを保持")
                coco = 1
            elif ball_color == "yellow":
                logger.info(f"黄色のボールを保持")
                coco = 2
            else:
                logger.info(f"赤色のボールを保持")
                coco = 3
                
            # 次のライントレースに備えて、カメラの解像度を下げてFPSを60に戻す
            logger.info("ライントレース用にカメラの解像度を戻します。")
            cam.set_resolution(1280, 720)
            
            for i in range(coco):
                tracer.run(cross = True)
                tracer.run(timeout=0.3)
            
            if coco == 1:
                omni.Movexy(0,600)
                servo_ctrl.set_angle(9, 60)
                omni.Movexy(0,-500)
                omni.turn()
                
            elif coco == 2:
                omni.turn(90)
                omni.Movexy(0,300)
                servo_ctrl.set_angle(9, 60)
                omni.Movexy(0,-200)
                omni.turn(90)
            
            elif coco == 3:
                omni.turn(90)
                omni.Movexy(0,300)
                servo_ctrl.set_angle(9, 60)
                omni.Movexy(0,-200)
                omni.turn(90)
                
            for i in range(coco):
                    tracer.run(cross = True)
                    tracer.run(timeout=0.3)

    except KeyboardInterrupt:
        logger.info("プログラムを終了します。")
    finally:
        serial_ctrl.close()
        cam.stop() # 終了時にカメラリソースを安全に解放する

# def turn_180(omni):
#     omni.rotation(1)
#     time.sleep(1.5)
#     omni.stop(calibrate=True)

# def turn_90(omni,wise =True):
#     if wise:
#         omni.rotation(1)
#     else:
#         omni.rotation(-1)
#     time.sleep(1)
#     omni.stop(calibrate=True)


def search_in_ballarea(omni,detector):
    toto=False
    for i in range(2):
        for j in range(2):
            omni.Movexy(-70,0)
            logger.info(f"ボールエリアの({j},{i})で探しています。")
            processed_frame, ball = detector.detect()
            if ball is not None:
                toto = True
                break
        if toto:
            break
        omni.Movexy(0,200)
    
    if not toto:
        logger.info("ボールが見つかりませんでした。")
        return None

    logger.info("ボールへの接近を開始します。")
    center_x = 3280 // 2
    center_y = 2400 // 2
    target_radius = 200 # ボールがこの大きさ(半径)になるまで近づく (実機に合わせて調整してください)
    kp_x = 0.0002 # ボールを中央に捉えるための回転ゲイン
    kp_y = 0.0002
    base_speed = 0.2 # 接近する際の前進速度

    while True:
        processed_frame, ball = detector.detect()
        
        if ball is None:
            omni.stop()
            logger.warning("ボールを見失いました！")
            break
            
        diff_x = ball['cx'] - center_x
        diff_y = ball['cy'] - center_y
        v_x = diff_x * kp_x
        
        # 画像の上方向（Y座標が小さい）にあるときに前進（プラス）させるため、符号を反転します
        v_y = -diff_y * kp_y
        
        if math.fabs(diff_x) <= 20 and math.fabs(diff_y) <= 20 :
            # ボールを中心にとらえた後、完全に停止させる
            omni.stop(calibrate=True)
            logger.info(f"ボールを中心にとらえました")
            return ball['color']
            
        omni.Speedxy(v_x,v_y)
        time.sleep(0.01)
    


if __name__ == "__main__":
    main()