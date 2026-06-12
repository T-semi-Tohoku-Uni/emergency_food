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

    def detect(self, crop=None, frame=None):
        # frameが渡されなかった場合、カメラから自動取得する
        if frame is None:
            if self.cam is None:
                # line_detectorと同じ解像度で初期化します
                self.cam = Camera(width=3280, height=2400)
            # ボールは床にあると想定し、必要に応じて切り取ります（デフォルトは全体）
            crop_area = crop if crop is not None else (0, 0, 3280, 2400)
            frame = self.cam.capture(crop=crop_area)

        # 色の判定をしやすくするため、BGRからHSV色空間に変換
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
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
                if cv2.contourArea(c) > 500:
                    # 輪郭を囲む最小の円を計算
                    ((x, y), radius) = cv2.minEnclosingCircle(c)
                    
                    # 重心の計算
                    M = cv2.moments(c)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        
                        # 見つけたボールの情報をリストに追加
                        detected_balls.append({
                            "color": color_name,
                            "cx": cx,
                            "cy": cy,
                            "radius": int(radius)
                        })
                        
                        # 結果を描画
                        cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2) # 黄色い円で囲む
                        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1) # 中心に赤い点
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