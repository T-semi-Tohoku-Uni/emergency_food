import time
import sys
import os

# このファイルの場所(tests)から見て、1つ上の階層(emergency_food_robot)をモジュール検索パスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# arm_controller.py ファイルから ArmController クラスをインポートする
# ※もし元のファイル名が異なる場合は、ここの「arm_controller」を実際のファイル名（.pyは除く）に変更してください。
from controllers.arm_controller import ArmController

def test_arm_controller():
    print("=== ArmController 動作確認テストを開始します ===")
    
    try:
        # 1. 初期化のテスト
        print("\n[テスト1] インスタンス化")
        arm = ArmController()
        print("結果: 成功")
        time.sleep(5) # サーボの移動を待機

        # 2. 正常値のテスト（安全な範囲内）
        test_len1, test_height1 = 120, 40
        print(f"\n[テスト2] 正常な位置への移動 (長さ: {test_len1}mm, 高さ: {test_height1}mm)")
        arm.set_position(test_len1, test_height1)
        print("結果: 成功 (エラーなし)")
        time.sleep(5) # サーボの移動を待機

        # 3. 正常値のテスト（境界値付近）
        test_len2, test_height2 = 130, 50
        print(f"\n[テスト3] 正常な位置への移動 (長さ: {test_len2}mm, 高さ: {test_height2}mm)")
        arm.set_position(test_len2, test_height2)
        print("結果: 成功 (エラーなし)")
        time.sleep(5)

        # 4. エラー処理のテスト（長さの上限オーバー）
        test_len3, test_height3 = 140, 20
        print(f"\n[テスト4] 限界値オーバーのテスト (長さ: {test_len3}mm, 高さ: {test_height3}mm)")
        try:
            arm.set_position(test_len3, test_height3)
            print("結果: 失敗 (ValueErrorが発生しませんでした)")
        except ValueError as e:
            print(f"結果: 成功 (期待通りエラーを捕捉) -> {e}")
        time.sleep(5)

        # 5. エラー処理のテスト（高さの下限アンダー）
        test_len4, test_height4 = 150, 10
        print(f"\n[テスト5] 限界値アンダーのテスト (長さ: {test_len4}mm, 高さ: {test_height4}mm)")
        try:
            arm.set_position(test_len4, test_height4)
            print("結果: 失敗 (ValueErrorが発生しませんでした)")
        except ValueError as e:
            print(f"結果: 成功 (期待通りエラーを捕捉) -> {e}")

    except Exception as e:
        print(f"\n予期せぬエラーでテストが中断されました: {e}")
        
    print("\n=== 全てのテストが完了しました ===")

if __name__ == "__main__":
    test_arm_controller()