import time
import math
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

import cv2
import numpy as np
from controllers.camera import Camera

def calculate_line_angle(contour):
    """OpenCVのfitLineを使って輪郭から直線の傾き（角度）を計算します"""
    [vx, vy, x0, y0] = cv2.fitLine(contour, cv2.DIST_L2, 0, 0.01, 0.01)
    if vy[0] != 0:
        return math.degrees(math.atan(vx[0] / vy[0]))
    else:
        return 0.0

def detect_line(frame):
    """画像フレームから線を検出し、その重心や傾きを返す"""

    # フレームが正しく取得できていない場合は処理をスキップ
    if frame is None:
        return frame, None, None, False, 0.0

    # 入力画像が1チャンネル（グレースケール）の場合、事前にBGRに変換しておく（OpenCVエラー対策）
    if len(frame.shape) == 2 or frame.shape[2] == 1:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    # 1. グレースケール変換
    gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
    
    # 2. ガウシアンブラーでノイズ除去 (5x5のカーネル)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # 3. 二値化（黒い線を抽出）
    _, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)

    # 4. 輪郭抽出 (RETR_EXTERNALを使うことで内部の輪郭探索を省き高速化)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        # 最も面積の大きい輪郭（ノイズではなく実際の線）を見つける
        c = max(contours, key=cv2.contourArea)
        
        # 5. 重心の計算 (画像モーメント)
        M = cv2.moments(c)
        if M["m00"] != 0:
            # 縮小画像上での重心
            small_cx = int(M["m10"] / M["m00"])
            small_cy = int(M["m01"] / M["m00"])
            
            # 元のスケールに座標を戻す
            cx = int(small_cx / scale)
            cy = int(small_cy / scale)
            
            # 線の傾き（角度）を計算
            angle_diff = calculate_line_angle(c)
            
            # 交差点（T字、十字）の判定
            x, y, w, h = cv2.boundingRect(c)
            
            # 幅と高さも元のスケールに戻して判定
            w_original = w / scale
            h_original = h / scale
            is_cross = False
            # 幅が画面の40%以上あり、かつ単なるノイズを誤認しないよう高さが20ピクセル以上あるかを確認
            if w > frame.shape[1] * 0.4 and h > 20:
                is_cross = True
                cv2.putText(frame, "CROSS DETECTED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            cv2.circle(frame, (cx, cy), 7, (0, 0, 255), -1)  # 重心に赤い点を打つ
            cv2.putText(frame, f"Angle: {angle_diff:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            
            # X座標(cx)が画面の中心からどれくらいズレているかが、ライントレースの要になります
            return frame, cx, cy, is_cross, angle_diff
            
    # 線が見つからなかった場合
    return frame, None, None, False, 0.0

# --- テスト実行用 ---
if __name__ == "__main__":
    # このスクリプトを直接実行した際のテストコード
    # カメラを初期化し、ライン検知を1回実行して結果を保存します。
    cam = None
    try:
        print("カメラを起動してライン検知テストを行います...")
        cam = Camera(width=3280, height=480)
        # 画像全体を使ってテスト
        frame = cam.capture()
        processed_frame, cx, cy, is_cross, angle_diff = detect_line(frame)

        if cx is not None:
            print(f"線を発見しました！ 重心座標: X={cx}, Y={cy}, 傾き: {angle_diff:.1f}")
        else:
            print("線が見つかりませんでした。")

        cv2.imwrite("test_result.jpg", processed_frame)
        print("結果の画像を 'test_result.jpg' として保存しました。")
    finally:
        if cam:
            cam.stop()