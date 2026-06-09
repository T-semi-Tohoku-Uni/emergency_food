import time
import serial
from contollers.i2c_controller import ServoController
from contollers.omni_controller import OmniSpeed

def main():
    print("セットアップを行います")

    # オムニの初期化
    omni = OmniSpeed()
    servo_ctrl =  ServoController()

    # シリアル通信の初期化 (環境に合わせてポート名を変更してください。例: Windowsなら 'COM3', Linuxなら '/dev/ttyACM0')
    serial_port = '/dev/ttyACM0' 
    baud_rate = 115200

    try:
        ser = serial.Serial(serial_port, baud_rate, timeout=0.1)
        print(f"シリアルポート {serial_port} に接続しました。")
    except serial.SerialException as e:
        print(f"シリアルポート接続エラー: {e}")
        return

    print("セットアップが完了しました。シリアルデータの受信を待機します（Ctrl+Cで終了）")

    try:
        while True:
            # 受信バッファにデータがあるか確認
            if ser.in_waiting > 0:
                # 1行読み込んで、不要な改行文字を削除
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if line:
                    print(f"受信データ: {line}")
                    
            time.sleep(0.01) # CPU負荷を下げるための短いウェイト

    except KeyboardInterrupt:
        print("\nプログラムを終了します。")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()