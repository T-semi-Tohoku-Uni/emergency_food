import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

import cv2
import numpy as np
from controllers.camera import Camera
from setup_logger import logger

class BallDetector:
    def __init__(self, camera_instance=None, color_ranges=None):
        self.cam = camera_instance
        
        if color_ranges is None:
            # 認識したいボールの色のHSV範囲を定義
            # [注意] 環境の明るさに合わせて、この範囲を調整する必要があります
            self.color_ranges = {
                "red": [
                    # 赤色はHSV空間の0付近と180付近に分かれるため、2つの範囲を定義します
                    ([0, 120, 70], [10, 255, 255]),
                    ([170, 120, 70], [180, 255, 255])
                ],
                "blue": [
                    ([100, 150, 0], [140, 255, 255])
                ],
                "yellow": [
                    ([20, 100, 100], [30, 255, 255])
                ]
            }
        else:
            self.color_ranges = color_ranges

        # 周波数(FPS)計測用の変数
        self.fps_start_time = time.time()
        self.frame_count = 0

    def detect(self, crop=None, frame=None):
        # --- 周波数(FPS)の計測とログ出力 ---
        self.frame_count += 1
        current_time = time.time()
        elapsed_fps_time = current_time - self.fps_start_time
        if elapsed_fps_time >= 1.0: # 1秒ごとに計算して出力
            fps = self.frame_count / elapsed_fps_time
            logger.info(f"ボール検知周波数: {fps:.1f} Hz")
            self.fps_start_time = current_time
            self.frame_count = 0
            
        # frameが渡されなかった場合、カメラから自動取得する
        if frame is None:
            if self.cam is None:
                # line_detectorと同じ解像度で初期化します
                self.cam = Camera(width=3280, height=2400)
            frame = self.cam.capture()

        # --- 高速化のためのリサイズ処理 ---
        # 画像処理の負荷を下げるため、画像を1/4に縮小して処理を行う
        scale = 0.25
        small_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)

        # 色の判定をしやすくするため、BGRからHSV色空間に変換
        hsv = cv2.cvtColor(small_frame, cv2.COLOR_BGR2HSV)
        
        detected_balls = [] # 見つかったボールの情報を格納するリスト

        # 定義したすべての色について順番に探す
        for color_name, ranges in self.color_ranges.items():
            # その色だけを抽出するマスク（白黒画像）を作成
            mask = np.zeros(hsv.shape[:2], dtype="uint8")
            for lower, upper in ranges:
                lower_np = np.array(lower, dtype="uint8")
                upper_np = np.array(upper, dtype="uint8")
                mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lower_np, upper_np))
            
            # ノイズ（小さな点）を除去
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)
            
            # 輪郭を見つける
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if len(contours) > 0:
                # その色の中で最も面積の大きい輪郭を見つける
                c = max(contours, key=cv2.contourArea)
                
                # 面積が小さすぎるものはノイズとして無視 (閾値500は実機に合わせて調整)
                # 縮小画像での面積を元のスケールに換算して判定する
                original_area = cv2.contourArea(c) / (scale ** 2)
                if original_area > 500:
                    # 輪郭を囲む最小の円を計算
                    ((small_x, small_y), small_radius) = cv2.minEnclosingCircle(c)
                    
                    # 重心の計算
                    M = cv2.moments(c)
                    if M["m00"] != 0:
                        small_cx = int(M["m10"] / M["m00"])
                        small_cy = int(M["m01"] / M["m00"])
                        
                        # 元のスケールに座標や半径を戻す
                        cx = int(small_cx / scale)
                        cy = int(small_cy / scale)
                        x = int(small_x / scale)
                        y = int(small_y / scale)
                        radius = int(small_radius / scale)
                        
                        # 見つけたボールの情報をリストに追加
                        detected_balls.append({
                            "color": color_name,
                            "cx": cx,
                            "cy": cy,
                            "radius": radius
                        })
                        
                        # 結果を描画
                        cv2.circle(frame, (x, y), radius, (0, 255, 255), 2) # 黄色い円で囲む
                        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)     # 中心に赤い点
                        cv2.putText(frame, f"{color_name} ({int(radius)})", (cx - 20, cy - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # 見つかったボールの中から、最も半径(radius)が大きいものを1つ選んで返す
        if detected_balls:
            biggest_ball = max(detected_balls, key=lambda b: b["radius"])
            logger.debug(f"一番大きなボールを検出しました: 色={biggest_ball['color']}, 半径={biggest_ball['radius']}")
            return frame, biggest_ball
        else:
            return frame, None

# --- テスト実行用 ---
if __name__ == "__main__":
    def run_ball_detection_test():
        print("カメラからボールを探します...")
        detector = BallDetector()
        processed_frame, ball = detector.detect()
        
        if ball is not None:
            print(f"一番大きなボール - 色: {ball['color']}, 重心: X={ball['cx']}, Y={ball['cy']}, 半径: {ball['radius']}")
        else:
            print("ボールは見つかりませんでした。")
            
        cv2.imwrite("ball_test_result.jpg", processed_frame)
        print("結果の画像を 'ball_test_result.jpg' として保存しました。")

    run_ball_detection_test()