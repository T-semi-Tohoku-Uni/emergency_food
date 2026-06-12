import time
import sys
import os
# パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from controllers.i2c_controller import ServoController
from controllers.serial_calibrator import SerialCalibrator

def calb_rot_servo_all():
    # ==========================================
    # テスト環境の設定（環境に合わせて変更してください）
    # ==========================================
    SERIAL_PORT = "/dev/ttyACM0" # 例: Windows="COM3", Linux/Mac="/dev/ttyUSB0"
    BAUDRATE = 115200
    
    # 全輪のチャンネルとコマンドのリスト
    CHANNELS = [1, 14, 15, 0]
    COMMANDS = ["vela", "velb", "velc", "veld"]

    print("=== 全輪同時キャリブレーションの動作テストを開始します ===")
    
    try:
        print("I2C ServoController を初期化中...")
        servo_ctrl = ServoController()
        
        print(f"SerialCalibrator を初期化中 (ポート: {SERIAL_PORT})...")
        calibrator = SerialCalibrator(servo_ctrl, port=SERIAL_PORT, baudrate=BAUDRATE)
        
        # ニュートラル（静止点）の同時キャリブレーション
        final_offsets = calibrator.calibrate_neutral_all(
            channels=CHANNELS, 
            command_signals=COMMANDS, 
            tolerance=0.5
        )
        print(f"\n-> 【結果】 最終オフセット: {final_offsets}")

        time.sleep(2) # サーボを落ち着かせるための待機

        # 回転速度の同時キャリブレーション
        final_scales = calibrator.calibrate_speed_all(
            channels=CHANNELS, 
            command_signals=COMMANDS, 
            test_speed=0.5, 
            target_velocity=30.0
        )
        print(f"\n-> 【結果】 最終速度スケール: {final_scales}")

        # キャリブレーション後の最終動作確認
        print("\n--- キャリブレーション後の全輪同時動作テスト ---")
        print("補正された速度(0.5)で全輪を 2秒間 回転させます...")
        for ch in CHANNELS:
            servo_ctrl.set_speed(ch, 0.5)
        time.sleep(2.0)
        
        final_offsets = calibrator.calibrate_neutral_all(
            channels=CHANNELS, 
            command_signals=COMMANDS, 
            tolerance=0.5
        )

        print("速度 0.0 で全輪を停止させます。完全に静止するか確認してください。")
        for ch in CHANNELS:
            servo_ctrl.set_speed(ch, 0.0)
        time.sleep(2.0)
        
        print("\nテストが正常に完了しました。")

    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        
    finally:
        # 終了時に必ずモーターを止めてI2Cをクリーンアップする
        if 'servo_ctrl' in locals():
            print("\nクリーンアップを実行して終了します...")
            for ch in CHANNELS:
                servo_ctrl.set_speed(ch, 0.0)
            servo_ctrl.cleanup()

if __name__ == "__main__":
    calb_rot_servo_all()