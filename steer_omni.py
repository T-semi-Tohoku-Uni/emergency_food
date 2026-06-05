import evdev
from contollers.omni_controller import OmniSpeed # 作成したクラスをインポート

# デッドゾーン（スティックの触れていない時のブレを無視する遊び）
DEADZONE = 10
CENTER = 128

def normalize_stick(value):
    """
    コントローラの0〜255の値を、-1.0 〜 1.0 に変換する関数
    """
    offset = value - CENTER
    if abs(offset) < DEADZONE:
        return 0.0
    return offset / 128.0

def main():
    # オムニホイール制御の初期化
    omni = OmniSpeed(max_speed=1.0)

    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    controller = None

    # DualSense（本体）を探す
    for device in devices:
        # "Wireless Controller"が含まれていて、かつ"Touchpad"や"Motion"が含まれていないものを本体とみなす
        if "Wireless Controller" in device.name and "Touchpad" not in device.name and "Motion" not in device.name:
            controller = device
            break

    if not controller:
        print("DualSenseが見つかりません。Bluetooth接続を確認してください。")
        return

    print(f"{controller.name} に接続しました。操縦を開始します。")
    print("左スティック: 前後左右移動 / 右スティック: 回転 / 終了: Ctrl+C")

    # スティックの現在値を保持する変数
    current_x = 0.0
    current_y = 0.0
    current_omega = 0.0

    try:
        for event in controller.read_loop():
            # アナログスティックの入力イベント
            if event.type == evdev.ecodes.EV_ABS:
                
                # 左スティック X軸 (左右)
                if event.code == evdev.ecodes.ABS_X:
                    current_x = normalize_stick(event.value)
                    
                # 左スティック Y軸 (上下) 
                # ※コントローラは上が0、下が255なのでマイナスをかけて反転させます
                elif event.code == evdev.ecodes.ABS_Y:
                    current_y = -normalize_stick(event.value)
                    
                # 右スティック X軸 (回転用)
                elif event.code == evdev.ecodes.ABS_RX:
                    current_omega = normalize_stick(event.value)

                # --- モーターへの出力処理 ---
                # 現在の仕様では Speedxy と rotation を連続で呼ぶと上書きされてしまうため、
                # 回転入力がある場合は rotation を優先し、なければ Speedxy を呼び出します。
                if abs(current_omega) > 0.0:
                    omni.rotation(current_omega)
                else:
                    omni.Speedxy(current_x, current_y)

    except KeyboardInterrupt:
        print("\nプログラムを終了します。モーターを停止します。")
        # 終了時にモーターを安全に停止
        omni.Speedxy(0, 0)

if __name__ == "__main__":
    main()