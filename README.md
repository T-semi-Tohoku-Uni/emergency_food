制作記事
https://t-semi.esa.io/posts/644

環境
ラズパイ3B
ラズパイOS Lite 64bit trixe

Arduino Nano(おそらく旧ブートローダー)

ライブラリ
sudo apt install libcamera-apps -y
sudo apt install python3-dev build-essential -y
pip install opencv-python smbus2 platformio pyserial
(オプション isort)
pip install Adafruit-Blinka adafruit-circuitpython-pca9685 adafruit-circuitpython-motor
sudo apt install evtest

必ずやること
venvを有効にするために必ず以下のコードを実行してから作業をする
source venv/bin/activate (抜けるときは deactivate を実行)