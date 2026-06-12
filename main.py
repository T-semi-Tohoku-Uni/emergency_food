import time
from contollers.i2c_controller import ServoController
from contollers.omni_controller import OmniSpeed
from contollers.serial_controller import SerialController
from setup_logger import logger

def main():
    logger.info("セットアップを行います")

    # オムニの初期化
    omni = OmniSpeed()
    servo_ctrl =  ServoController()

    # シリアル通信の初期化 (環境に合わせてポート名を変更してください。例: Windowsなら 'COM3', Linuxなら '/dev/ttyACM0')
    serial_port = '/dev/ttyACM0' 
    baud_rate = 115200

    serial_ctrl = SerialController(port=serial_port, baud_rate=baud_rate)
    if not serial_ctrl.is_open():
        return

    logger.info("セットアップが完了しました。'start robot!' の受信を待機します（Ctrl+Cで終了）")
    
    try:
        # "start robot!" を検知するまで待機するループ
        while True:
            # ※ 注意: SerialController に受信データを文字列で取得するメソッド (例: read_line) があると想定しています。
            # 実装に合わせて適切なメソッドに変更してください。
            received_data = serial_ctrl.read_line() 
            
            if received_data and "start robot!" in received_data:
                logger.info("'start robot!' を検知しました。ロボットのメイン動作を開始します！")
                break # 待機ループを抜けてメイン処理へ進む
                
            time.sleep(0.5) # 待機中のCPU負荷を下げるためのウェイト

        # "start robot!" 検知後のメインループ
        omni.Movexy(200,0)

        

    except KeyboardInterrupt:
        logger.info("プログラムを終了します。")
    finally:
        serial_ctrl.close()

if __name__ == "__main__":
    main()