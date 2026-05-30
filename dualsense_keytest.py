import evdev

# 接続されているすべての入力デバイスを取得
devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
controller = None

# DualSense（本体）を探す
for device in devices:
    # "Wireless Controller"が含まれていて、かつ"Touchpad"や"Motion"が含まれていないものを本体とみなす
    if "Wireless Controller" in device.name and "Touchpad" not in device.name and "Motion" not in device.name:
        controller = device
        break

if not controller:
    print("コントローラが見つかりません。Bluetooth接続を確認してください。")
    exit()

print(f"接続成功: {controller.name}")
print("ボタンを押してみてください（終了は Ctrl+C）")

# 入力を監視するループ
try:
    for event in controller.read_loop():
        # ボタンが押された・離された時のイベント(EV_KEY)だけを抽出
        if event.type == evdev.ecodes.EV_KEY:
            # categorize() を使うと「×ボタン(BTN_SOUTH)が押された」などを分かりやすくテキストにしてくれます
            print(evdev.categorize(event))
            
        # ※もしアナログスティックの入力も見たい場合は、下の2行の # を消してください
        #elif event.type == evdev.ecodes.EV_ABS:
        #    print(evdev.categorize(event))

except KeyboardInterrupt:
    print("\nテストを終了します。")