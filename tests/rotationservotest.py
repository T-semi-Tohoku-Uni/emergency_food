import time
from controllers.i2c_controller import ServoController

def main():
    print("ロボットのシステムを起動します...")
    
    # サーボコントローラーの初期化
    servo_ctrl = ServoController()

    try:
        # 例：PCA9685の「0番」ピンに繋いだサーボを動かすテスト
        channel = 14

        print("反時計回り(CCW)で回転します...")
        # throttle > 0 (1500~2300 µsecの範囲)
        servo_ctrl.set_speed(channel, 1.0) 
        time.sleep(2)

        print("停止します...")
        # throttle = 0 (1500 µsec)
        servo_ctrl.set_speed(channel, 0.0) 
        time.sleep(2)

        print("時計回り(CW)で回転します...")
        # throttle < 0 (1500~700 µsecの範囲)
        servo_ctrl.set_speed(channel, -1.0) 
        time.sleep(2)

        print("ゆっくり反時計回りで回転します...")
        servo_ctrl.set_speed(channel, 0.5) 
        time.sleep(2)

        print("停止します...")
        # throttle = 0 (1500 µsec)
        servo_ctrl.set_speed(channel, 0) 
        time.sleep(2)

    except KeyboardInterrupt:
        # Ctrl+Cで停止したときの処理
        print("\nユーザーによってプログラムが停止されました。")
    
    finally:
        # プログラム終了時にI2Cの通信を安全に閉じる
        servo_ctrl.cleanup()
        print("システムを安全に終了しました。")

if __name__ == "__main__":
    main()