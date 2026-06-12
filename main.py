import time
from controllers.i2c_controller import ServoController
from controllers.omni_controller import OmniSpeed
from controllers.serial_controller import SerialController
from controllers.arm_controller import ArmController
from controllers.line_detector import detect_line
from setup_logger import logger

def main():
    logger.info("セットアップを行います")

    # オムニの初期化
    omni = OmniSpeed()
    servo_ctrl =  ServoController()
    arm = ArmController()
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
        logger.info("ライントレースを開始します！")
        
        # カメラの画像幅が 3280 のため、その中心である 1640 を基準にする
        center_x = 3280 // 2  
        base_speed = 0.3      # 前進する基本速度 (0.0 〜 1.0)
        kp = 0.0005           # 曲がりやすさの調整ゲイン (実機に合わせて調整してください)

        while True:
            # 画面の下半分を切り取って線を検知
            processed_frame, cx, cy = detect_line(crop=(0, 240, 3280, 240))
            
            if cx is not None:
                # 画像の中心からどれくらいズレているかを計算
                diff = cx - center_x
                
                # ズレの量に kp (ゲイン) を掛けて、回転速度(omega)を算出
                # ※ ロボットが逆方向に曲がる場合は kp をマイナス(-0.0005)にしてください
                omega = diff * kp
                
                # x(左右)=0, y(前進)=base_speed で前進しつつ、omega で回転して軌道修正
                omni.Speedxy_rotation(0, base_speed, omega)
                
            else:
                # 線が見つからない場合は安全のため停止
                omni.Speedxy(0, 0)
                
            time.sleep(0.05)

    except KeyboardInterrupt:
        logger.info("プログラムを終了します。")
    finally:
        serial_ctrl.close()

if __name__ == "__main__":
    main()