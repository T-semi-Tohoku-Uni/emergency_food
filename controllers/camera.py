from picamera2 import Picamera2
import time

class Camera:
    def __init__(self, width=640, height=480):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(main={"size": (width, height)})
        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(2) # カメラの露出やホワイトバランスが安定するまで待機

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

def main():
    cam = Camera(width=640, height=480)
    try:
        print("画像をキャプチャします...")
        image_array = cam.capture()
        print(f"画像を取得しました！ サイズ: {image_array.shape}")

        # 切り取りのテスト (例: x=100, y=100 の位置から 幅200, 高さ100 を切り取る)
        cropped_image = cam.capture(crop=(100, 100, 200, 100))
        print(f"切り取った画像サイズ: {cropped_image.shape}")

    finally:
        cam.stop()
        print("カメラを停止しました。")

if __name__ == "__main__":
    main()