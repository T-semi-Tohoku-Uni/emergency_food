import logging
from logging.handlers import RotatingFileHandler
import os

# マウント先が実在するか確認（USBが抜けている時のエラー回避）
log_dir = '/mnt/usb_logs'
if not os.path.ismount(log_dir):
    print("Warning: USBメモリがマウントされていません。ローカル(./logs)に保存します。")
    log_dir = './logs'  # フォールバック先のディレクトリに変更

# ロガーのセットアップ
logger = logging.getLogger('RobotLogger')
logger.setLevel(logging.INFO)

if not logger.handlers:
    # ログを保存するディレクトリが存在しない場合は自動作成する
    os.makedirs(log_dir, exist_ok=True)

    # 最大5MBのファイルを3世代まで残す設定
    handler = RotatingFileHandler(
        f'{log_dir}/emergency_food_robot_main.log', 
        maxBytes=5*1024*1024, 
        backupCount=3
    )
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # コンソール(標準出力)にも表示する設定
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # ログの書き込み
    logger.info("loggerのセットアップの終了")