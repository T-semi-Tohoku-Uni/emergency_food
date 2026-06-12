import time
import sys
import os
# パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")
import serial
from controllers.i2c_controller import ServoController

class SerialCalibrator:
    def __init__(self, servo_ctrl: ServoController, port: str, baudrate: int = 115200):
        """
        シリアル通信を使ってサーボのキャリブレーションを行うクラス
        port: シリアルポート（例: "COM3" または "/dev/ttyUSB0"）
        """
        self.servo_ctrl = servo_ctrl
        self.serial = serial.Serial(port, baudrate, timeout=1.0)
        time.sleep(2) # シリアル接続の確立待ち

    def get_velocity(self, command_signal: str) -> float:
        """
        指定した信号をシリアル通信で送り、返ってきた速度を読み取る
        """
        # 通信のズレを防ぐため、送信前にバッファをクリア
        self.serial.reset_input_buffer()
        
        # 信号を送信 (改行コードは環境に合わせて調整してください)
        self.serial.write((command_signal + '\n').encode('utf-8'))
        
        time.sleep(0.01) # マイコンが処理して返答するのを少し待つ

        # 送り返された速度を受信
        line = self.serial.readline().decode('utf-8').strip()
        try:
            return float(line)
        except ValueError:
            print(f"警告: 速度の読み取りに失敗しました (受信内容: '{line}')")
            return 0.0

    def calibrate_neutral(self, channel: int, command_signal: str, tolerance: float = 0.5):
        """
        サーボの静止点（ニュートラルパルス）をキャリブレーションする
        速度が許容範囲内(tolerance)に収まるまでオフセットを調整する
        """
        print(f"チャンネル {channel} のニュートラルキャリブレーションを開始します...")
        offset = 0
        self.servo_ctrl.set_calibration_offset(channel, offset)
        self.servo_ctrl.set_speed(channel, 0.0) # 停止指令を送る
        time.sleep(1.0) # サーボが安定するまで待機

        # フィードバックループで0に近づける（最大20回繰り返す）
        for i in range(20):
            velocity = self.get_velocity(command_signal)
            print(f"現在の速度: {velocity}, 現在のオフセット: {offset}")

            if abs(velocity) <= tolerance:
                print(f"ニュートラル調整完了: 最終オフセット {offset}us")
                return offset

            # 速度がプラスかマイナスかに応じてパルスを微調整
            # ※ 実際のモーターやエンコーダの極性に合わせて +/- を逆にしてください
            if velocity > 0:
                offset -= 10
            else:
                offset += 10

            self.servo_ctrl.set_calibration_offset(channel, offset)
            self.servo_ctrl.set_speed(channel, 0.0)
            time.sleep(1)

        print("完全な静止には至りませんでしたが、最も近い値で終了します。")
        return offset

    def calibrate_speed(self, channel: int, command_signal: str, test_speed: float = 0.5, target_velocity: float = 50.0):
        """
        サーボの回転速度をキャリブレーションする
        指令値に対する実際の速度を測定し、個体差を補正するためのスケール係数を算出する
        """
        print(f"チャンネル {channel} の速度キャリブレーションを開始します...")
        self.servo_ctrl.set_speed_scale(channel, 1.0) # 一旦スケールをリセット
        
        self.servo_ctrl.set_speed(channel, test_speed)
        time.sleep(1.0)
        
        velocity = self.get_velocity(command_signal)
        print(f"指令値 {test_speed} での実際の速度: {velocity}")
        
        self.servo_ctrl.set_speed(channel, 0.0)
        
        if velocity == 0:
            print("エラー: モーターが回転していないか、速度が0です。")
            return 1.0

        # 理想の速度と実際の速度の比をスケールとする
        scale = target_velocity / velocity
        print(f"算出した速度スケール係数: {scale:.3f}")
        
        self.servo_ctrl.set_speed_scale(channel, scale)
        return scale

    def calibrate_neutral_all(self, channels: list, command_signals: list, tolerance: float = 0.5):
        """
        複数のサーボの静止点（ニュートラルパルス）を同時にキャリブレーションする
        """
        print("全チャンネルのニュートラルキャリブレーションを開始します...")
        offsets = {ch: 0 for ch in channels}
        
        for ch in channels:
            self.servo_ctrl.set_calibration_offset(ch, 0)
            self.servo_ctrl.set_speed(ch, 0.0) # 全てに停止指令を送る
            
        time.sleep(1.0) # サーボが安定するまで待機

        active_channels = channels.copy()
        
        for i in range(20):
            if not active_channels:
                break
                
            for ch, cmd in zip(channels, command_signals):
                if ch not in active_channels:
                    continue
                    
                velocity = self.get_velocity(cmd)
                print(f"[Ch {ch}] 現在の速度: {velocity}, 現在のオフセット: {offsets[ch]}")

                if abs(velocity) <= tolerance:
                    print(f"-> Ch {ch} ニュートラル調整完了: 最終オフセット {offsets[ch]}us")
                    active_channels.remove(ch)
                else:
                    if velocity > 0:
                        offsets[ch] -= 10
                    else:
                        offsets[ch] += 10

                    self.servo_ctrl.set_calibration_offset(ch, offsets[ch])
                    self.servo_ctrl.set_speed(ch, 0.0)
                    
            time.sleep(0.5)

        if active_channels:
            print(f"一部のチャンネルで完全な静止に至りませんでした: {active_channels}")
            
        return offsets

    def calibrate_speed_all(self, channels: list, command_signals: list, test_speed: float = 0.5, target_velocity: float = 50.0):
        """
        複数のサーボの回転速度を同時にキャリブレーションする
        """
        print("全チャンネルの速度キャリブレーションを開始します...")
        scales = {}
        
        for ch in channels:
            self.servo_ctrl.set_speed_scale(ch, 1.0) # 一旦スケールをリセット
            self.servo_ctrl.set_speed(ch, test_speed)
            
        time.sleep(1.0)
        
        for ch, cmd in zip(channels, command_signals):
            velocity = self.get_velocity(cmd)
            print(f"[Ch {ch}] 指令値 {test_speed} での実際の速度: {velocity}")
            
            if velocity == 0:
                print(f"エラー: Ch {ch} モーターが回転していないか、速度が0です。")
                scales[ch] = 1.0
            else:
                scale = target_velocity / velocity
                print(f"-> Ch {ch} 算出した速度スケール係数: {scale:.3f}")
                scales[ch] = scale
                self.servo_ctrl.set_speed_scale(ch, scale)
                
        for ch in channels:
            self.servo_ctrl.set_speed(ch, 0.0)
            
        return scales