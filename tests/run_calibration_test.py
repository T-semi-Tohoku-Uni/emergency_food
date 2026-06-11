import time
import sys
import os
# パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from controllers.i2c_controller import ServoController
from controllers.serial_calibrator import SerialCalibrator

def calb_rot_servo(wheel=1,channel=1,command="vela"):
    # ==========================================
    # テスト環境の設定（環境に合わせて変更してください）
    # ==========================================
    SERIAL_PORT = "/dev/ttyACM0" # 例: Windows="COM3", Linux/Mac="/dev/ttyUSB0"
    BAUDRATE = 115200
    
    # テスト対象のサーボ設定 (OmniControllerの場合は 0, 1, 14, 15 などを指定)
    TEST_CHANNEL = channel
    COMMAND_SIGNAL = command # マイコン側に送る速度要求コマンド
    if wheel == 1:
        TEST_CHANNEL = 1
        COMMAND_SIGNAL = "vela"
    elif wheel == 2:
        TEST_CHANNEL = 14
        COMMAND_SIGNAL = "velb"
    elif wheel == 3:
        TEST_CHANNEL = 15
        COMMAND_SIGNAL = "velc"
    elif wheel == 4:
        TEST_CHANNEL = 0
        COMMAND_SIGNAL = "veld"


    print("=== キャリブレーションの動作テストを開始します ===")
    
    try:
        # 1. コントローラーとキャリブレーターの初期化
        print("I2C ServoController を初期化中...")
        servo_ctrl = ServoController()
        
        print(f"SerialCalibrator を初期化中 (ポート: {SERIAL_PORT})...")
        calibrator = SerialCalibrator(servo_ctrl, port=SERIAL_PORT, baudrate=BAUDRATE)
        
        # 2. ニュートラル（静止点）のキャリブレーション
        print(f"\n--- チャンネル {TEST_CHANNEL} のニュートラル(静止点)キャリブレーション ---")
        final_offset = calibrator.calibrate_neutral(
            channel=TEST_CHANNEL, 
            command_signal=COMMAND_SIGNAL, 
            tolerance=0.5
        )
        print(f"-> 【結果】 チャンネル {TEST_CHANNEL} の最終オフセット: {final_offset} us")

        time.sleep(2) # サーボを落ち着かせるための待機

        # 3. 回転速度のキャリブレーション
        print(f"\n--- チャンネル {TEST_CHANNEL} の回転速度キャリブレーション ---")
        # test_speed はモーターを回す指令値 (0.0 ~ 1.0)
        # target_velocity はその test_speed で本来出てほしい理想の速度
        final_scale = calibrator.calibrate_speed(
            channel=TEST_CHANNEL, 
            command_signal=COMMAND_SIGNAL, 
            test_speed=0.5, 
            target_velocity=30.0
        )
        print(f"-> 【結果】 チャンネル {TEST_CHANNEL} の最終速度スケール: {final_scale:.3f}")

        # 4. キャリブレーション後の最終動作確認
        print("\n--- キャリブレーション後の動作テスト ---")
        print("補正された速度(0.5)で 2秒間 回転させます...")
        servo_ctrl.set_speed(TEST_CHANNEL, 0.5)
        time.sleep(2.0)
        
        print("速度 0.0 で停止させます。完全に静止するか確認してください。")
        servo_ctrl.set_speed(TEST_CHANNEL, 0.0)
        time.sleep(2.0)
        
        print("\nテストが正常に完了しました。")

    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        
    finally:
        # 終了時に必ずモーターを止めてI2Cをクリーンアップする
        if 'servo_ctrl' in locals():
            print("\nクリーンアップを実行して終了します...")
            servo_ctrl.set_speed(TEST_CHANNEL, 0.0)
            servo_ctrl.cleanup()

if __name__ == "__main__":
    calb_rot_servo(1)
    calb_rot_servo(2)
    calb_rot_servo(3)
    calb_rot_servo(4)