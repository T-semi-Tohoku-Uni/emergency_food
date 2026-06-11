import serial
from setup_logger import logger

class SerialController:
    def __init__(self, port='/dev/ttyACM0', baud_rate=115200, timeout=0.1):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.ser = None

        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            logger.info(f"シリアルポート {self.port} に接続しました。")
        except serial.SerialException as e:
            logger.error(f"シリアルポート接続エラー: {e}")

    def is_open(self):
        return self.ser is not None and self.ser.is_open

    def close(self):
        if self.is_open():
            self.ser.close()

    def check_incoming(self):
        """受信バッファを確認し、データがあれば読み込んで返します"""
        if self.is_open() and self.ser.in_waiting > 0:
            line = self.ser.readline().decode('utf-8', errors='replace').strip()
            if line:
                logger.info(f"受信データ: {line}")
                return line
        return None

    def send_and_receive_command(self, command):
        """特定の信号（コマンド）を送信し、相手からの返答を受け取ります"""
        if not self.is_open():
            return None
        self.ser.reset_input_buffer()
        self.ser.write((command + '\n').encode('utf-8'))
        logger.info(f"信号を送信しました: {command}")
        response = self.ser.readline().decode('utf-8', errors='replace').strip()
        if response:
            logger.info(f"返答を受信しました: {response}")
            return response
        return None