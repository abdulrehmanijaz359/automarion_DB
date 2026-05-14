import snap7
from snap7.util import *
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *
import time

class PLCWriter:
    def __init__(self, plc_connection):
        self.plc = plc_connection

    def write_int(self, db_number, offset, value):
        try:
            data = bytearray(2)
            set_int(data, 0, value)
            self.plc.client.db_write(db_number, offset, data)
            return True
        except Exception as e:
            print(f"❌ Write error: {e}")
            return False

    def send_command(self, action, level, row, col):
        try:
            print(f"\n📤 Sending to PLC:")
            print(f"   Action={action} Level={level} Row={row} Col={col}")

            self.write_int(DB_COMMAND, OFFSET_ACTION, action)
            self.write_int(DB_COMMAND, OFFSET_LEVEL,  level)
            self.write_int(DB_COMMAND, OFFSET_ROW,    row)
            self.write_int(DB_COMMAND, OFFSET_COL,    col)

            print(f"   ✅ Command sent to DB{DB_COMMAND}!")
            return True
        except Exception as e:
            print(f"❌ Send command error: {e}")
            return False

    def send_home(self):
        print("\n🏠 Sending HOME command...")
        return self.send_command(ACTION_HOME, 0, 0, 0)