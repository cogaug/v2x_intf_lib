import sys
import time
import argparse
from v2xintf import V2XInterface, WAVE_MSG_IDS

# Try to import PyQt6 to demonstrate integration
try:
        from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QLabel
        from PyQt6.QtCore import pyqtSignal, QObject
        HAS_PYQT6 = True
except ImportError:
        HAS_PYQT6 = False

def get_msg_info(msg_id: int):
        for entry in WAVE_MSG_IDS:
            if int(entry["dsrc_msg_id"]) == msg_id:
                return entry
        return None

if HAS_PYQT6:
        # 1. Define a QObject adapter to bridge the background thread callback to a Qt signal
        class QtReceiverAdapter(QObject):
            packetReceived = pyqtSignal(bytes, int)
            def on_packet(self, data: bytes, msg_id: int):
                self.packetReceived.emit(data, msg_id)

        # 2. Create a simple Demo Window
        class DemoWindow(QMainWindow):
            def __init__(self, remote_address="127.0.0.1", remote_port=1516, local_port=5398):
                super().__init__()
                self.setWindowTitle("V2XInterface PyQt6 Demo")
                self.resize(600, 400)
                central = QWidget()
                self.setCentralWidget(central)
                layout = QVBoxLayout(central)
                
                self.lbl_status = QLabel(f"Listening on port {local_port}...")
                layout.addWidget(self.lbl_status)
                self.txt_log = QTextEdit()
                self.txt_log.setReadOnly(True)
                layout.addWidget(self.txt_log)

                # Setup adapter and receiver
                self.adapter = QtReceiverAdapter()
                self.adapter.packetReceived.connect(self.on_packet_received)
                
                self.v2x_interface = V2XInterface(callback=self.adapter.on_packet, remote_address=remote_address, remote_port=remote_port, local_port=local_port)
                self.v2x_interface.start()

            def on_packet_received(self, data: bytes, msg_id: int):
                msg_info = get_msg_info(msg_id)
                msg_name = "Unknown"
                if msg_info is not None:
                    msg_name = msg_info["name"]
                
                msg = f"Received packet: {len(data)} bytes, {msg_name} (Message ID: {msg_id})."
                self.txt_log.append(msg)
                data_hex = " ".join(f"{b:02x}" for b in data)
                self.txt_log.append(f"Data (hex): {data_hex}\n")
                self.v2x_interface.sendV2XMessage(data) # Echo back the received message for testing send functionality

            def closeEvent(self, event):
                self.v2x_interface.stop()
                super().closeEvent(event)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="V2XInterface Example")
    parser.add_argument("--remote-address", type=str, default="127.0.0.1", help="Remote IP address (default: 127.0.0.1)")
    parser.add_argument("--remote-port", type=int, default=1516, help="Remote UDP port (default: 1516)")
    parser.add_argument("--local-port", type=int, default=5398, help="Local UDP port (default: 5398)")
    args = parser.parse_args()

    if HAS_PYQT6:
        # Replace sys.argv to remove parsed arguments so QApplication doesn't complain
        app = QApplication([sys.argv[0]]) 
        win = DemoWindow(remote_address=args.remote_address, remote_port=args.remote_port, local_port=args.local_port)
        win.show()
        print(f"Running PyQt6 demo (Listening on port {args.local_port}, remote target {args.remote_address}:{args.remote_port})")
        sys.exit(app.exec())

    else:
        # callback: Console-only test
        def test_callback(data: bytes, msg_id: int):
            msg_info = get_msg_info(msg_id)
            msg_name = "Unknown"
            if msg_info is not None:
                msg_name = msg_info["name"]
                
            data_hex = " ".join(f"{b:02x}" for b in data)
            print(f"Received packet: {len(data)} bytes, {msg_name} (Message ID: {msg_id}).")
            print(f"Data (hex): {data_hex}\n")              
# TODO: Uncomment the line below to test sending functionality (echo back the received message)
#            v2x_interface.sendV2XMessage(data) # Echo back the received message for testing send functionality

        print(f"Starting console-only V2XInterface test on port {args.local_port}...")
        v2x_interface = V2XInterface(callback=test_callback, remote_address=args.remote_address, remote_port=args.remote_port, local_port=args.local_port)
        v2x_interface.start()

        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping receiver...")
            v2x_interface.stop()
            print("Done.")
