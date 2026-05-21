# README

## 制作記事
- [InRoF2026日誌(#644](https://t-semi.esa.io/posts/644)

## 動作環境
- **SBC:** Raspberry Pi 3 Model B
- **OS:** Raspberry Pi OS Lite (64bit, trixie)
- **Microcontroller:** Arduino Nano (おそらく旧ブートローダー)

## 必ずやること
作業を開始する前に**必ず仮想環境（venv）を有効化**する。

```bash
# 仮想環境の有効化
source venv/bin/activate
```

※ 仮想環境を終了（無効化）する。
```bash
deactivate
```

## 必要ライブラリのインストール
仮想環境が有効な状態で、以下の必要なライブラリをインストールする。

### 1. システムパッケージ（apt）(これは仮想環境外で)
```bash
sudo apt update
sudo apt install libcamera-apps -y
sudo apt install python3-dev build-essential -y
```

### 2. Pythonパッケージ（pip）
isortは必須じゃない
```bash
pip install opencv-python smbus2 platformio pyserial
pip install Adafruit-Blinka adafruit-circuitpython-pca9685 adafruit-circuitpython-motor
pip install isort
```
