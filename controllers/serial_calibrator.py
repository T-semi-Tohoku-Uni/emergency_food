import time
import serial
from controllers.i2c_controller import ServoController

class SerialCalibrator:
    def __init__(self, servo_ctrl: ServoController, port: str, baudrate: int = 115200):
        """
        シリアル通信を使ってサーボのキャリブレーションを行うクラスを初期化
        
        Args:
            servo_ctrl (ServoController): サーボコントローラのインスタンス
            port (str): シリアルポート（例: "COM3" または "/dev/ttyUSB0"）
            baudrate (int): ボーレート（デフォルト: 115200）
        """
        self.servo_ctrl = servo_ctrl
        self.serial = serial.Serial(port, baudrate, timeout=1.0)
        time.sleep(2) # シリアル接続の確立待ち

    def get_velocity(self, command_signal: str) -> float:
        """
        指定したコマンド信号をシリアル通信で送り、返ってきた速度を読み取る
        
        Args:
            command_signal (str): マイコンに送るコマンド文字列
        
        Returns:
            float: マイコンから返された速度値（失敗時は 0.0）
        """
        # 信号を送信 (改行コードは環境に合わせて調整してください)
        self.serial.write((command_signal + '\n').encode('utf-8'))
        
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
        
        マイコンに指定コマンドを送り、返ってきた速度がほぼ0になるまで
        オフセット値を調整する
        
        Args:
            channel (int): キャリブレーション対象チャンネル
            command_signal (str): マイコンに送るコマンド文字列
            tolerance (float): 許容誤差（この値以下なら目標達成）
        
        Returns:
            int: 最終的に調整されたオフセット値（マイクロ秒）
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
            time.sleep(0.5)

        print("完全な静止には至りませんでしたが、最も近い値で終了します。")
        return offset

    def calibrate_speed(self, channel: int, command_signal: str, test_speed: float = 0.5, target_velocity: float = 50.0):
        """
        サーボの回転速度をキャリブレーションする
        
        指定した test_speed で指令を送り、実際の速度を測定して
        理想速度（target_velocity）に合わせるためのスケール係数を算出する
        
        Args:
            channel (int): キャリブレーション対象チャンネル
            command_signal (str): マイコンに送るコマンド文字列
            test_speed (float): テスト時の指令速度（-1.0 ~ 1.0）
            target_velocity (float): 目標速度（この値に合わせるよう補正）
        
        Returns:
            float: 算出されたスケール係数
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