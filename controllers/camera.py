from picamera2 import Picamera2
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")
from setup_logger import logger

class Camera:
    def __init__(self, width=3280, height=480):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(main={"size": (width, height)})
        self.picam2.configure(config)
        # センサーが許す限りの高いフレームレート（最大60fpsなど）を設定
        self.picam2.set_controls({"FrameRate": 60})
        self.picam2.start()
        time.sleep(2) # カメラの露出やホワイトバランスが安定するまで待機
        logger.info("カメラを起動しました。")

    def set_resolution(self, width, height):
        """カメラの解像度を動的に変更する"""
        logger.info(f"カメラの解像度を {width}x{height} に変更しています...")
        self.picam2.stop()
        config = self.picam2.create_preview_configuration(main={"size": (width, height)})
        self.picam2.configure(config)
        
        # 解像度が高いと60fpsでエラーになるため、フレームレートを安全な値に下げる
        fps = 15 if height > 1000 else 60
        self.picam2.set_controls({"FrameRate": fps})
            
        self.picam2.start()
        time.sleep(2) # 設定反映待ち
        logger.info(f"カメラの解像度変更が完了しました (FPS: {fps})。")

    def capture(self, crop=None):
        """画像をNumPy配列（OpenCV形式）で取得して返す
        crop: (x, y, width, height) の形式で指定すると、その範囲を切り取って返す
        """
        image = self.picam2.capture_array()
        if crop is not None:
            x, y, w, h = crop
            image = image[y:y+h, x:x+w] # NumPy配列のスライス機能で切り取る
        return image

    def stop(self):
        self.picam2.stop()
        logger.info("カメラを停止しました。")

def main():
    cam = Camera(width=3280, height=480)
    try:
        print("画像をキャプチャします...")
        image_array = cam.capture()
        print(f"画像を取得しました！ サイズ: {image_array.shape}")

    finally:
        cam.stop()
        print("カメラを停止しました。")

if __name__ == "__main__":
    main()