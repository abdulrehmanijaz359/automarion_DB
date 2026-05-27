import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

class PLCSimulator:
    def __init__(self):
        self.db11 = {
            'action': 0,
            'level' : 0,
            'row'   : 0,
            'col'   : 0
        }
        self.db12 = {
            'gripper_status': GRIPPER_IDLE,
            'current_level' : 0,
            'current_row'   : 0,
            'current_col'   : 0
        }
        self.connected = True
        print("PLC Simulator started!")
        print("(Replace with real PLC when available)")

    def connect(self):
        self.connected = True
        print("Simulator connected!")
        return True

    def disconnect(self):
        self.connected = False
        print("Simulator disconnected!")

    def is_connected(self):
        return self.connected

    def reset(self):
        self.db12['gripper_status'] = GRIPPER_IDLE
        self.db12['current_level']  = 0
        self.db12['current_row']    = 0
        self.db12['current_col']    = 0
        print("Simulator reset to IDLE!")

    def send_command(self, action, level, row, col):
        print(f"\nSimulator received command:")
        print(f"  Action={action} Level={level} Row={row} Col={col}")

        self.db11['action'] = action
        self.db11['level']  = level
        self.db11['row']    = row
        self.db11['col']    = col

        self.db12['gripper_status'] = GRIPPER_MOVING
        self.db12['current_level']  = level
        self.db12['current_row']    = row
        self.db12['current_col']    = col

        move_time = 1 if action == ACTION_HOME else 2
        print(f"  Gripper moving... ({move_time}s)")
        time.sleep(move_time)

        self.db12['gripper_status'] = GRIPPER_DONE
        print(f"  Gripper done!")
        return True

    def send_home(self):
        print("\nSimulator going HOME...")
        return self.send_command(ACTION_HOME, 0, 0, 0)

    def get_gripper_status(self):
        return self.db12['gripper_status']

    def get_current_position(self):
        return (
            self.db12['current_level'],
            self.db12['current_row'],
            self.db12['current_col']
        )

    def wait_for_done(self, timeout=COMMAND_TIMEOUT):
        print("Waiting for gripper...")
        start = time.time()
        while True:
            status = self.get_gripper_status()
            if status == GRIPPER_DONE:
                print("Done!")
                return True
            elif status == GRIPPER_ERROR:
                print("Error!")
                return False
            elif time.time() - start > timeout:
                print("Timeout!")
                return False
            time.sleep(POLL_INTERVAL)

    def wait_for_home(self, timeout=COMMAND_TIMEOUT):
        print("Waiting for HOME...")
        start = time.time()
        while True:
            status = self.get_gripper_status()
            if status == GRIPPER_IDLE:
                print("At HOME!")
                return True
            elif status == GRIPPER_ERROR:
                print("Error at HOME!")
                return False
            elif time.time() - start > timeout:
                print("HOME timeout!")
                return False
            time.sleep(POLL_INTERVAL)

    def simulate_error(self):
        self.db12['gripper_status'] = GRIPPER_ERROR
        print("Simulated error triggered!")