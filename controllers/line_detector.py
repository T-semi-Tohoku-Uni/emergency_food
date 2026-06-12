import time
import math
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

import cv2
import numpy as np
from controllers.camera import Camera

# カメラのインスタンスを保持するグローバル変数
_cam_instance = None

def detect_line(crop=None, cross=False, frame=None):
    global _cam_instance
    # frameが渡されなかった場合、カメラから自動取得する
    if frame is None:
        if _cam_instance is None:
            _cam_instance = Camera(width=320, height=240)
        crop_area = crop if crop is not None else (0, 120, 320, 120)
        frame = _cam_instance.capture(crop=crop_area)

    # 1. グレースケール変換
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 2. ガウシアンブラーでノイズ除去 (5x5のカーネル)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # 3. 二値化（黒い線を抽出）
    # 背景が白、線が黒の場合。環境の明るさに合わせて閾値(ここでは60)を調整してください。
    # cv2.THRESH_BINARY_INV を使うことで、黒い線を「白(255)」として抽出します。
    _, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        # 最も面積の大きい輪郭（ノイズではなく実際の線）を見つける
        c = max(contours, key=cv2.contourArea)
        
        # 5. 重心の計算 (画像モーメント)
        M = cv2.moments(c)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            
            # 結果をわかりやすく描画 (元のフレームに上書き)
            cv2.drawContours(frame, [c], -1, (0, 255, 0), 2) # 抽出した輪郭を緑色で囲む
            cv2.circle(frame, (cx, cy), 7, (0, 0, 255), -1)  # 重心に赤い点を打つ
            
            # X座標(cx)が画面の中心からどれくらいズレているかが、ライントレースの要になります
            return frame, cx, cy
            
    # 線が見つからなかった場合
    return frame, None, None

# --- テスト実行用（Webカメラ等の映像を読み込む場合） ---
if __name__ == "__main__":
    # cap = cv2.VideoCapture(0) # 0番のカメラを起動
    
    # テスト用のダミー画像（真っ白な背景に黒い線を引いたもの）を作成
    test_image = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    # 線の検出を実行
    result_frame, cx, cy = detect_line(frame=test_image)
    
    if cx is not None:
        print(f"線の重心が見つかりました: X={cx}, Y={cy}")
    
    # 画像を表示
    cv2.imshow("Line Detection", result_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()