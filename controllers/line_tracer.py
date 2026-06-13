import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from setup_logger import logger
from controllers.line_detector import detect_line

class LineTracer:
    def __init__(self, omni, serial_ctrl, camera, base_speed=0.3, kp=0.5, ki=0.0, kd=1.5, debug=False):
        """
        ライントレースを実行するクラス
        omni: OmniSpeedインスタンス
        serial_ctrl: SerialControllerインスタンス
        camera: Cameraインスタンス（複数起動によるリソース競合を防ぐため外部から渡す）
        base_speed: 前進する基本速度
        kp: 比例ゲイン（現在のズレに対する修正力）
        ki: 積分ゲイン（過去のズレの蓄積に対する修正力）
        kd: 微分ゲイン（ズレの変化量に対する修正力、振動を抑える）
        """
        self.omni = omni
        self.serial_ctrl = serial_ctrl
        self.camera = camera
        self.base_speed = base_speed
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.debug = debug
        
        # 中心位置はカメラから画像を取得した際に動的に決定する
        self.center_x = None 

        # PID制御用の変数
        self.last_diff = 0.0
        self.integral = 0.0
        self.integral_limit = 1000.0  # 積分値のワインドアップ対策（上限・下限）

        # 線を見失っている状態かどうかのフラグ（再発見時の暴走対策）
        self.line_lost = True

        # 実行状態を管理するフラグ
        self.is_running = False

    def set_pid(self, kp, ki, kd):
        """PIDパラメータを実行中に動的に変更する"""
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.integral = 0.0
        self.last_diff = 0.0
        logger.info(f"PIDパラメータを更新しました: Kp={self.kp}, Ki={self.ki}, Kd={self.kd}")

    def stop(self):
        """外部からライントレースを強制的に終了させるメソッド"""
        self.is_running = False

    def run(self, timeout=None,cross = False):
        """
        ライントレースを実行する
        timeout: 指定した秒数(float)が経過すると自動で終了する。Noneの場合は無限に走り続ける。
        """
        if timeout is not None:
            logger.info(f"ライントレースを開始します！（{timeout}秒間）")
        else:
            logger.info("ライントレースを開始します！")
        self.is_running = True
        start_time = time.time()
        
        # 周波数(FPS)計測用の変数
        fps_start_time = time.time()
        frame_count = 0

        while self.is_running:
            # タイムアウトのチェック
            if timeout is not None and (time.time() - start_time) >= timeout:
                logger.info(f"指定された時間（{timeout}秒）が経過したため、ライントレースを終了します。")
                self.stop()
                continue

            # シリアル通信からの終了信号（再度 "start robot!"）をチェック
            received_data = self.serial_ctrl.check_incoming()
            if received_data and "start robot!" in received_data:
                logger.info("再度 'start robot!' を検知しました。ライントレースを終了し、ロボットを停止します。")
                self.stop()
                continue # 次のループ条件の判定に進み、ループを抜ける

            # 画像全体を使って線を検知
            frame = self.camera.capture()
            
            # 取得した画像の幅から動的に中心位置を計算する（左に曲がり続けるバグの対策）
            if frame is not None:
                self.center_x = frame.shape[1] // 2
                
            processed_frame, cx, cy, is_cross, angle_diff = detect_line(frame)
            
            if cx is not None:
                if is_cross:
                    logger.info("交差点(T字または十字)を検知しました！")
                    # --- ここに交差点検知時の処理を書くことができます ---
                    # 例1: 交差点でライントレースを終了させる場合
                    if cross:
                        self.stop()
                        continue
                    else:
                        # 交差点通過中は横線の影響を無視するため、姿勢制御(PID)を行わず直進のみとする
                        self.omni.Speedxy_rotation(0, self.base_speed, 0.0)
                        time.sleep(0.01)
                        continue

                # 画像の中心からのズレを算出
                # 画像サイズによらず同じ割合のズレとして扱えるように、相対値（-1.0 〜 1.0）に正規化
                diff = (cx - self.center_x) / self.center_x
                
                # 線を再発見した直後は、前回のdiffが存在しないためD項が暴走するのを防ぐ
                if self.line_lost:
                    self.last_diff = diff
                    self.line_lost = False

                # PID制御の計算
                self.integral += diff
                
                # アンチワインドアップ（積分項が大きくなりすぎるのを防ぐ）
                if self.integral > self.integral_limit:
                    self.integral = self.integral_limit
                elif self.integral < -self.integral_limit:
                    self.integral = -self.integral_limit

                derivative = diff - self.last_diff
                
                p_term = diff * self.kp
                i_term = self.integral * self.ki
                d_term = derivative * self.kd
                omega = p_term + i_term + d_term
                
                # 回転の力が強すぎてその場でスピンするのを防ぐため、omegaの最大値/最小値を制限
                omega = max(-0.5, min(0.5, omega))
                
                self.last_diff = diff
                
                if self.debug:
                    logger.info(f"Diff:{diff:7.4f} | P:{p_term:7.4f} I:{i_term:7.4f} D:{d_term:7.4f} | Omega:{omega:7.4f}")
                
                self.omni.Speedxy_rotation(0, self.base_speed, omega)
            else:
                # 線が見つからない場合は安全のため停止
                self.integral = 0.0
                # last_diff は 0 にリセットせず、再発見時の暴走を防ぐためにフラグを立てる
                self.line_lost = True
                self.omni.Speedxy(0, 0, smooth=False)
                
            # サンプリング周期を上げるため待機時間を短縮（0.05 -> 0.01）
            time.sleep(0.01)

            # --- 周波数(FPS)の計測とログ出力 ---
            frame_count += 1
            current_time = time.time()
            elapsed_fps_time = current_time - fps_start_time
            if elapsed_fps_time >= 1.0: # 1秒ごとに計算して出力
                fps = frame_count / elapsed_fps_time
                logger.info(f"ライントレース周波数: {fps:.1f} Hz")
                fps_start_time = current_time
                frame_count = 0


        # ループを抜けた後（ライントレース終了時）に必ずモーターを停止させる
        self.omni.Speedxy(0, 0, smooth=False)


# --- テスト実行用 ---
if __name__ == "__main__":
    from controllers.serial_controller import SerialController
    from controllers.i2c_controller import ServoController
    from controllers.omni_controller import OmniSpeed
    from controllers.camera import Camera

    def test_line_tracer():
        logger.info("=== LineTracer 動作確認テストを開始します ===")
        
        # シリアル通信の初期化
        serial_ctrl = SerialController(port='/dev/ttyACM0', baud_rate=115200)
        if not serial_ctrl.is_open():
            logger.error("シリアルポートを開けませんでした。Picoが接続されているか確認してください。")
            return
            
        # その他のコントローラーの初期化
        servo_ctrl = ServoController()
        omni = OmniSpeed(servo_ctrl=servo_ctrl, serial_instance=serial_ctrl.ser)
        cam = Camera(width=3280, height=180) # ライントレース用の解像度で初期化
        
        # LineTracerのインスタンス化 (テスト用にdebug=Trueでログを詳細に出力)
        tracer = LineTracer(omni=omni, serial_ctrl=serial_ctrl, camera=cam, base_speed=0.3, debug=True)
        
        try:
            logger.info("ライントレースを開始します。(停止するには Ctrl+C を押してください)")
            # 交差点検知で止まるように実行
            tracer.run(cross=True)
            logger.info("交差点を検知したため停止しました。")
        except KeyboardInterrupt:
            logger.info("\nユーザー操作によりテストを中断しました。")
        finally:
            omni.stop()
            servo_ctrl.cleanup()
            cam.stop()
            serial_ctrl.close()
            logger.info("システムを安全に終了しました。")

    test_line_tracer()
