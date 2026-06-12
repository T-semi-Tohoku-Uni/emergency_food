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

def calculate_line_angle(contour):
    """OpenCVのfitLineを使って輪郭から直線の傾き（角度）を計算します"""
    [vx, vy, x0, y0] = cv2.fitLine(contour, cv2.DIST_L2, 0, 0.01, 0.01)
    if vy[0] != 0:
        return math.degrees(math.atan(vx[0] / vy[0]))
    else:
        return 0.0

def detect_line(crop=None, cross=False, frame=None):
    global _cam_instance
    # frameが渡されなかった場合、カメラから自動取得する
    if frame is None:
        if _cam_instance is None:
            _cam_instance = Camera(width=3280, height=480)
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
            
            # 線の傾き（角度）を計算
            angle_diff = calculate_line_angle(c)
            
            # 交差点（T字、十字）の判定
            # 外接矩形を取得し、その幅(w)が画像全体の幅の 70% 以上なら交差点とみなす
            x, y, w, h = cv2.boundingRect(c)
            is_cross = False
            if w > frame.shape[1] * 0.7:
                is_cross = True
                cv2.putText(frame, "CROSS DETECTED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # 結果をわかりやすく描画 (元のフレームに上書き)
            cv2.drawContours(frame, [c], -1, (0, 255, 0), 2) # 抽出した輪郭を緑色で囲む
            cv2.circle(frame, (cx, cy), 7, (0, 0, 255), -1)  # 重心に赤い点を打つ
            cv2.putText(frame, f"Angle: {angle_diff:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            
            # X座標(cx)が画面の中心からどれくらいズレているかが、ライントレースの要になります
            return frame, cx, cy, is_cross, angle_diff
            
    # 線が見つからなかった場合
    return frame, None, None, False, 0.0

# --- テスト実行用 ---
if __name__ == "__main__":
    def test_with_dummy_image():
        print("テスト用のダミー画像を作成して検知テストを行います...")
        
        # 背景が真っ白(255)の画像(高さ240, 幅320)を作成
        # test_image = np.ones((240, 320, 3), dtype=np.uint8) * 255
        
        # テストとして、X=100 の位置に縦に黒(0,0,0)の直線を引く (太さ10ピクセル)
        # cv2.line(test_image, (100, 0), (100, 240), (0, 0, 0), 10)
        
        # 線の検出を実行（frame引数にテスト画像を渡すのでカメラは起動しません）
        processed_frame, cx, cy, is_cross, angle_diff = detect_line(crop = (0, 240, 3280, 240))
        
        if cx is not None:
            print(f"線を発見しました！ 重心座標: X={cx}, Y={cy}")
            if cx == 100:
                print("テスト成功: 描画した線の位置(X=100)を正しく認識しました。")
            if is_cross:
                print("交差点を検知しました！")
                
        else:
            print("線が見つかりませんでした。テスト失敗です。")
        
        # 処理結果の画像をファイルとして保存する
        cv2.imwrite("test_result.jpg", processed_frame)
        print("結果の画像を 'test_result.jpg' として保存しました。")

    test_with_dummy_image()