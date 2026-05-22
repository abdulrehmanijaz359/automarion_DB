import snap7
from snap7.util import *
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

class PLCConnection:
    def __init__(self):
        self.client    = snap7.client.Client()
        self.connected = False

    def connect(self):
        try:
            self.client.connect(PLC_IP, PLC_RACK, PLC_SLOT)
            if self.client.get_connected():
                self.connected = True
                print(f"✅ Connected to PLC at {PLC_IP}")
                return True
            else:
                print("❌ Connection failed!")
                return False
        except Exception as e:
            print(f"❌ PLC Connection Error: {e}")
            self.connected = False
            return False

    def disconnect(self):
        try:
            self.client.disconnect()
            self.connected = False
            print("👋 Disconnected from PLC!")
        except Exception as e:
            print(f"❌ Disconnect Error: {e}")

    def is_connected(self):
        try:
            return self.client.get_connected()
        except:
            return False

    def reconnect(self):
        print("🔄 Trying to reconnect to PLC...")
        self.disconnect()
        return self.connect()

    def send_command(self, action, level, row, col):
        try:
            print(f"\n📤 Sending to PLC:")
            print(f"   Action={action} Level={level} Row={row} Col={col}")

            for offset, value in [
                (OFFSET_ACTION, action),
                (OFFSET_LEVEL,  level),
                (OFFSET_ROW,    row),
                (OFFSET_COL,    col)
            ]:
                data = bytearray(2)
                set_int(data, 0, value)
                self.client.db_write(DB_COMMAND, offset, data)

            print(f"   ✅ Command sent to DB{DB_COMMAND}!")
            return True
        except Exception as e:
            print(f"❌ Send command error: {e}")
            return False

    def send_home(self):
        print("\n🏠 Sending HOME command...")
        return self.send_command(ACTION_HOME, 0, 0, 0)

    def get_gripper_status(self):
        try:
            data = self.client.db_read(DB_STATUS, OFFSET_GRIPPER, 2)
            return get_int(data, 0)
        except Exception as e:
            print(f"❌ Read error: {e}")
            return None

    def wait_for_done(self, timeout=COMMAND_TIMEOUT):
        import time
        print("⏳ Waiting for gripper to finish...")
        start = time.time()
        while True:
            status = self.get_gripper_status()
            if status == GRIPPER_DONE:
                print("✅ Gripper done!")
                return True
            elif status == GRIPPER_ERROR:
                print("❌ Gripper error!")
                return False
            elif time.time() - start > timeout:
                print("❌ Command timed out!")
                return False
            time.sleep(POLL_INTERVAL)

    def wait_for_home(self, timeout=COMMAND_TIMEOUT):
        import time
        print("⏳ Waiting for gripper to reach HOME...")
        start = time.time()
        while True:
            status = self.get_gripper_status()
            if status == GRIPPER_IDLE:
                print("✅ Gripper at HOME!")
                return True
            elif status == GRIPPER_ERROR:
                print("❌ Gripper error at HOME!")
                return False
            elif time.time() - start > timeout:
                print("❌ HOME command timed out!")
                return False
            time.sleep(POLL_INTERVAL)