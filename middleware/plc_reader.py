import snap7
from snap7.util import *
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *
import time

class PLCReader:
    def __init__(self, plc_connection):
        self.plc = plc_connection

    def read_int(self, db_number, offset):
        try:
            data = self.plc.client.db_read(db_number, offset, 2)
            return get_int(data, 0)
        except Exception as e:
            print(f"❌ Read error: {e}")
            return None

    def get_gripper_status(self):
        return self.read_int(DB_STATUS, OFFSET_GRIPPER)

    def get_current_position(self):
        level = self.read_int(DB_STATUS, OFFSET_CURR_LEVEL)
        row   = self.read_int(DB_STATUS, OFFSET_CURR_ROW)
        col   = self.read_int(DB_STATUS, OFFSET_CURR_COL)
        return level, row, col

    def wait_for_done(self, timeout=COMMAND_TIMEOUT):
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