import time
from contollers.i2c_controller import ServoController

def main():
    print("ロボットのシステムを起動します...")
    
    # サーボコントローラーの初期化
    servo_ctrl = ServoController()

    try:
        # 例：PCA9685の「0番」ピンに繋いだサーボを動かすテスト
        target_channel = 0

        print("0度へ移動")
        servo_ctrl.set_angle(target_channel, 0)
        time.sleep(1)

        print("90度へ移動")
        servo_ctrl.set_angle(target_channel, 90)
        time.sleep(1)

        print("180度へ移動")
        servo_ctrl.set_angle(target_channel, 180)
        time.sleep(1)

        print("90度へ戻る")
        servo_ctrl.set_angle(target_channel, 90)
        time.sleep(1)

    except KeyboardInterrupt:
        # Ctrl+Cで停止したときの処理
        print("\nユーザーによってプログラムが停止されました。")
    
    finally:
        # プログラム終了時にI2Cの通信を安全に閉じる
        servo_ctrl.cleanup()
        print("システムを安全に終了しました。")

if __name__ == "__main__":
    main()