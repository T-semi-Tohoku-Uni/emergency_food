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

    logger.info("セットアップが完了しました。シリアルデータの受信を待機します（Ctrl+Cで終了）")

    try:
        while True:
            # 受信バッファにデータがあるか確認して処理
            serial_ctrl.check_incoming()
                    
            time.sleep(0.01) # CPU負荷を下げるための短いウェイト
    
    
        
            # 例として "PING" という特定の信号を送信し、返答を受け取ります
            # ※実際に相手側が待っている文字列に変更してください
            reply = serial_ctrl.send_and_receive_command("PING")
            
            if reply:
                # 返答に応じた処理（ロボットの制御など）をここに記述します
                pass
            else:
                logger.warning("返答がありませんでした")
                
            # 連続して送信しすぎないよう待機時間を設けます
            time.sleep(1.0)

    except KeyboardInterrupt:
        logger.info("プログラムを終了します。")
    finally:
        serial_ctrl.close()

if __name__ == "__main__":
    main()