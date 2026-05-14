import mysql.connector
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

class BlockingLogic:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        self.cursor = self.conn.cursor(dictionary=True)

    def get_slot(self, level, row, col):
        self.cursor.execute("""
            SELECT * FROM slots
            WHERE level=%s AND row_num=%s AND col_num=%s
        """, (level, row, col))
        return self.cursor.fetchone()

    def get_blocking_slots(self, level, row, col):
        blocking = []

        if level == 'A':
            # Check B and C
            slot_b = self.get_slot('B', row, col)
            slot_c = self.get_slot('C', row, col)
            if slot_b and slot_b['status'] == 'occupied':
                blocking.append(slot_b)
            if slot_c and slot_c['status'] == 'occupied':
                blocking.append(slot_c)

        elif level == 'B':
            # Check C only
            slot_c = self.get_slot('C', row, col)
            if slot_c and slot_c['status'] == 'occupied':
                blocking.append(slot_c)

        elif level == 'C':
            # Nothing blocks C
            pass

        return blocking

    def get_reserved_slots(self):
        self.cursor.execute("""
            SELECT * FROM slots
            WHERE slot_type='reserved' AND status='empty'
        """)
        return self.cursor.fetchall()

    def check_access(self, level, row, col):
        # Get blocking slots
        blocking = self.get_blocking_slots(level, row, col)

        if not blocking:
            return True, [], "Slot is accessible"

        # Check if we have enough reserved slots
        reserved = self.get_reserved_slots()

        if len(reserved) >= len(blocking):
            return True, blocking, f"{len(blocking)} slot(s) need relocation"
        else:
            return False, blocking, f"Not enough reserved slots! Need {len(blocking)}, have {len(reserved)}"