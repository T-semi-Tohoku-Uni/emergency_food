import time
from i2c_controller import ServoController
from omni_controller import OmniSpeed

def main():
    print("オムニの動作確認を行います...")

    # オムニの初期化
    omni = OmniSpeed()
    servo_ctrl =  ServoController()

    try:
        # 例：PCA9685の「0番」ピンに繋いだサーボを動かすテスト
        target_channel = 0

        print("Speedxy")
        omni.Speedxy(10,10)
        time.sleep(10)

        print("SpeedPolar")
        omni.SpeedPolar(10,0)
        time.sleep(10)

        print("rotation")
        omni.rotation(10)
        time.sleep(10)

        print("stop")
        #omni.rotation(0)
        omni.SpeedPolar(0,0)
        time.sleep(10)

    except KeyboardInterrupt:
        # Ctrl+Cで停止したときの処理
        print("\nユーザーによってプログラムが停止されました。")
    
    finally:
        # プログラム終了時にI2Cの通信を安全に閉じる
        servo_ctrl.cleanup()
        print("システムを安全に終了しました。")

if __name__ == "__main__":
    main()
