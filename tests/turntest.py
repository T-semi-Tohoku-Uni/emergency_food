import time
import sys
import os
# パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from controllers.i2c_controller import ServoController
from controllers.omni_controller import OmniSpeed

def main():
    print("オムニの動作確認を行います...")

    # オムニの初期化
    omni = OmniSpeed()
    servo_ctrl =  ServoController()

    try:
        # 例：PCA9685の「0番」ピンに繋いだサーボを動かすテスト
        target_channel = 0

        print("180 右")
        omni.turn(180,True)
        time.sleep(1)
        
        print("90 右")
        omni.turn(90,True)
        time.sleep(1)

        print("180 左")
        omni.turn(180,False)
        time.sleep(1)

        print("90 左")
        omni.turn(180,False)
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