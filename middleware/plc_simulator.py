import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

class PLCSimulator:
    """
    Simulates the S7-1200 PLC behavior.
    Used for testing when real PLC is not available.
    When real PLC is ready, just replace this with
    PLCConnection + PLCWriter + PLCReader.
    """

    def __init__(self):
        # Simulate DB11 — command block
        self.db11 = {
            'action' : 0,
            'level'  : 0,
            'row'    : 0,
            'col'    : 0
        }

        # Simulate DB12 — status block
        self.db12 = {
            'gripper_status' : GRIPPER_IDLE,
            'current_level'  : 0,
            'current_row'    : 0,
            'current_col'    : 0
        }

        self.connected = True
        print("🤖 PLC Simulator started!")
        print("   (Replace with real PLC when available)")

    # ─────────────────────────────────────
    # CONNECTION
    # ─────────────────────────────────────

    def connect(self):
        self.connected = True
        print("✅ Simulator connected!")
        return True

    def disconnect(self):
        self.connected = False
        print("👋 Simulator disconnected!")

    def is_connected(self):
        return self.connected

    # ─────────────────────────────────────
    # WRITE TO DB11 (receive commands)
    # ─────────────────────────────────────

    def send_command(self, action, level, row, col):
        print(f"\n📤 Simulator received command:")
        print(f"   Action={action} Level={level} Row={row} Col={col}")

        self.db11['action'] = action
        self.db11['level']  = level
        self.db11['row']    = row
        self.db11['col']    = col

        # Simulate gripper moving
        self.db12['gripper_status'] = GRIPPER_MOVING
        self.db12['current_level']  = level
        self.db12['current_row']    = row
        self.db12['current_col']    = col

        # Simulate movement time
        if action == ACTION_HOME:
            move_time = 1  # 1 second to go home
        else:
            move_time = 2  # 2 seconds for pick/place

        print(f"   🤖 Gripper moving... ({move_time}s)")
        time.sleep(move_time)

        # Simulate done
        self.db12['gripper_status'] = GRIPPER_DONE
        print(f"   ✅ Gripper done!")
        return True

    def send_home(self):
        print("\n🏠 Simulator going HOME...")
        return self.send_command(ACTION_HOME, 0, 0, 0)

    # ─────────────────────────────────────
    # READ FROM DB12 (get status)
    # ─────────────────────────────────────

    def get_gripper_status(self):
        return self.db12['gripper_status']

    def get_current_position(self):
        return (
            self.db12['current_level'],
            self.db12['current_row'],
            self.db12['current_col']
        )

    def wait_for_done(self, timeout=COMMAND_TIMEOUT):
        print("⏳ Waiting for gripper...")
        start = time.time()
        while True:
            status = self.get_gripper_status()

            if status == GRIPPER_DONE:
                print("✅ Done!")
                return True

            elif status == GRIPPER_ERROR:
                print("❌ Error!")
                return False

            elif time.time() - start > timeout:
                print("❌ Timeout!")
                return False

            time.sleep(POLL_INTERVAL)

    def wait_for_home(self, timeout=COMMAND_TIMEOUT):
        print("⏳ Waiting for HOME...")
        start = time.time()
        while True:
            status = self.get_gripper_status()

            if status == GRIPPER_IDLE:
                print("✅ At HOME!")
                return True

            elif status == GRIPPER_ERROR:
                print("❌ Error at HOME!")
                return False

            elif time.time() - start > timeout:
                print("❌ HOME timeout!")
                return False

            time.sleep(POLL_INTERVAL)

    def simulate_error(self):
        """Call this to test error handling"""
        self.db12['gripper_status'] = GRIPPER_ERROR
        print("⚠️ Simulated error triggered!")