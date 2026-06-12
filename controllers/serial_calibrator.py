import time
import sys
import os
# パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")
import serial
from controllers.i2c_controller import ServoController
from setup_logger import logger

class SerialCalibrator:
    def __init__(self, servo_ctrl: ServoController, port: str = None, baudrate: int = 115200, serial_instance=None):
        """
        シリアル通信を使ってサーボのキャリブレーションを行うクラス
        port: シリアルポート（例: "COM3" または "/dev/ttyUSB0"）
        serial_instance: すでに開いているserial.Serialインスタンスがある場合はこちらを渡す
        """
        self.servo_ctrl = servo_ctrl
        if serial_instance is not None:
            self.serial = serial_instance
        else:
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
            logger.warning(f"速度の読み取りに失敗しました (受信内容: '{line}')")
            return 0.0

    def calibrate_neutral(self, channel: int, command_signal: str, tolerance: float = 0.5):
        """
        サーボの静止点（ニュートラルパルス）をキャリブレーションする
        速度が許容範囲内(tolerance)に収まるまでオフセットを調整する
        """
        logger.info(f"チャンネル {channel} のニュートラルキャリブレーションを開始します...")
        offset = 0
        self.servo_ctrl.set_calibration_offset(channel, offset)
        self.servo_ctrl.set_speed(channel, 0.0) # 停止指令を送る
        time.sleep(1.0) # サーボが安定するまで待機

        # フィードバックループで0に近づける（最大20回繰り返す）
        for i in range(20):
            velocity = self.get_velocity(command_signal)
            logger.debug(f"現在の速度: {velocity}, 現在のオフセット: {offset}")

            if abs(velocity) <= tolerance:
                logger.info(f"チャンネル {channel} のニュートラル調整完了: 最終オフセット {offset}us")
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

        logger.warning(f"チャンネル {channel}: 完全な静止には至りませんでしたが、最も近い値で終了します。")
        return offset

    def calibrate_speed(self, channel: int, command_signal: str, test_speed: float = 0.5, target_velocity: float = 50.0):
        """
        サーボの回転速度を正転・逆転両方でキャリブレーションする
        指令値に対する実際の速度を測定し、個体差を補正するためのスケール係数を正転・逆転それぞれ算出する
        """
        logger.info(f"チャンネル {channel} の速度キャリブレーションを開始します...")
        self.servo_ctrl.set_speed_scale(channel, 1.0, 1.0) # 一旦スケールをリセット
        
        # 正転のキャリブレーション
        self.servo_ctrl.set_speed(channel, test_speed)
        time.sleep(1.0)
        fw_velocity = self.get_velocity(command_signal)
        logger.debug(f"正転 指令値 {test_speed} での実際の速度: {fw_velocity}")
        self.servo_ctrl.set_speed(channel, 0.0)
        time.sleep(0.5)

        # 逆転のキャリブレーション
        self.servo_ctrl.set_speed(channel, -test_speed)
        time.sleep(1.0)
        bw_velocity = self.get_velocity(command_signal)
        logger.debug(f"逆転 指令値 {-test_speed} での実際の速度: {bw_velocity}")
        self.servo_ctrl.set_speed(channel, 0.0)
        
        scale_fw = 1.0
        scale_bw = 1.0

        if fw_velocity == 0:
            logger.error("正転時にモーターが回転していないか、速度が0です。")
        else:
            scale_fw = abs(target_velocity / fw_velocity)

        if bw_velocity == 0:
            logger.error("逆転時にモーターが回転していないか、速度が0です。")
        else:
            scale_bw = abs(target_velocity / bw_velocity)

        logger.info(f"チャンネル {channel} の算出した速度スケール係数 -> 正転: {scale_fw:.3f}, 逆転: {scale_bw:.3f}")
        
        self.servo_ctrl.set_speed_scale(channel, scale_forward=scale_fw, scale_backward=scale_bw)
        return scale_fw, scale_bw

    def calibrate_neutral_all(self, channels: list, command_signals: list, tolerance: float = 0.5):
        """
        複数のサーボの静止点（ニュートラルパルス）を同時にキャリブレーションする
        """
        logger.info("全チャンネルのニュートラルキャリブレーションを開始します...")
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
                logger.debug(f"[Ch {ch}] 現在の速度: {velocity}, 現在のオフセット: {offsets[ch]}")

                if abs(velocity) <= tolerance:
                    logger.info(f"-> Ch {ch} ニュートラル調整完了: 最終オフセット {offsets[ch]}us")
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
            logger.warning(f"一部のチャンネルで完全な静止に至りませんでした: {active_channels}")
            
        return offsets

    def calibrate_speed_all(self, channels: list, command_signals: list, test_speed: float = 0.5, target_velocity: float = 50.0):
        """
        複数のサーボの回転速度を正転・逆転両方で同時にキャリブレーションする
        """
        logger.info("全チャンネルの速度キャリブレーション(正転・逆転)を開始します...")
        scales_fw = {}
        scales_bw = {}
        
        for ch in channels:
            self.servo_ctrl.set_speed_scale(ch, 1.0, 1.0) # 一旦スケールをリセット
            
        # --- 正転の測定 ---
        for ch in channels:
            self.servo_ctrl.set_speed(ch, test_speed)
        time.sleep(1.0)
        
        for ch, cmd in zip(channels, command_signals):
            velocity = self.get_velocity(cmd)
            logger.debug(f"[Ch {ch}] 正転 指令値 {test_speed} での実際の速度: {velocity}")
            if velocity == 0:
                logger.error(f"Ch {ch} 正転時にモーターが回転していないか、速度が0です。")
                scales_fw[ch] = 1.0
            else:
                scales_fw[ch] = abs(target_velocity / velocity)

        for ch in channels:
            self.servo_ctrl.set_speed(ch, 0.0)
        time.sleep(1.0)

        # --- 逆転の測定 ---
        for ch in channels:
            self.servo_ctrl.set_speed(ch, -test_speed)
        time.sleep(1.0)

        for ch, cmd in zip(channels, command_signals):
            velocity = self.get_velocity(cmd)
            logger.debug(f"[Ch {ch}] 逆転 指令値 {-test_speed} での実際の速度: {velocity}")
            if velocity == 0:
                logger.error(f"Ch {ch} 逆転時にモーターが回転していないか、速度が0です。")
                scales_bw[ch] = 1.0
            else:
                scales_bw[ch] = abs(target_velocity / velocity)

        for ch in channels:
            self.servo_ctrl.set_speed(ch, 0.0)
            logger.info(f"-> Ch {ch} 算出した速度スケール係数 - 正転: {scales_fw[ch]:.3f}, 逆転: {scales_bw[ch]:.3f}")
            self.servo_ctrl.set_speed_scale(ch, scale_forward=scales_fw[ch], scale_backward=scales_bw[ch])
            
        return scales_fw, scales_bw