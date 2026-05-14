import snap7
from snap7.util import *
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

class PLCConnection:
    def __init__(self):
        self.client = snap7.client.Client()
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