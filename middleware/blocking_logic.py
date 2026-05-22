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
        """
        Returns list of slots that must be
        removed before accessing target slot.
        C is on top of B which is on top of A.
        To get A: remove C first then B.
        To get B: remove C first.
        To get C: nothing blocking.
        """
        blocking = []

        if level == 'A':
            # Remove C first then B
            slot_c = self.get_slot('C', row, col)
            slot_b = self.get_slot('B', row, col)
            if slot_c and slot_c['status'] == 'occupied':
                blocking.append(slot_c)
            if slot_b and slot_b['status'] == 'occupied':
                blocking.append(slot_b)

        elif level == 'B':
            # Remove C first
            slot_c = self.get_slot('C', row, col)
            if slot_c and slot_c['status'] == 'occupied':
                blocking.append(slot_c)

        elif level == 'C':
            # Nothing blocks C — always accessible
            pass

        return blocking

    def can_store(self, level, row, col):
        """
        Check if we can store an item at this slot.
        A can always be stored if empty.
        B can only be stored if A is occupied.
        C can only be stored if both A and B are occupied.
        """
        if level == 'A':
            slot_a = self.get_slot('A', row, col)
            if slot_a and slot_a['status'] == 'occupied':
                return False, f"A({row},{col}) is already occupied!"
            return True, "OK"

        elif level == 'B':
            slot_a = self.get_slot('A', row, col)
            slot_b = self.get_slot('B', row, col)
            if not slot_a or slot_a['status'] == 'empty':
                return False, \
                    f"Cannot store in B({row},{col}) — " \
                    f"A({row},{col}) is empty! Fill A first."
            if slot_b and slot_b['status'] == 'occupied':
                return False, f"B({row},{col}) is already occupied!"
            return True, "OK"

        elif level == 'C':
            slot_a = self.get_slot('A', row, col)
            slot_b = self.get_slot('B', row, col)
            slot_c = self.get_slot('C', row, col)
            if not slot_a or slot_a['status'] == 'empty':
                return False, \
                    f"Cannot store in C({row},{col}) — " \
                    f"A({row},{col}) is empty! Fill A first."
            if not slot_b or slot_b['status'] == 'empty':
                return False, \
                    f"Cannot store in C({row},{col}) — " \
                    f"B({row},{col}) is empty! Fill B first."
            if slot_c and slot_c['status'] == 'occupied':
                return False, f"C({row},{col}) is already occupied!"
            return True, "OK"

        return False, "Invalid level!"

    def get_reserved_slots(self):
        self.cursor.execute("""
            SELECT * FROM slots
            WHERE slot_type='reserved' AND status='empty'
            ORDER BY row_num ASC
        """)
        return self.cursor.fetchall()

    def check_access(self, level, row, col):
        blocking = self.get_blocking_slots(level, row, col)

        if not blocking:
            return True, [], "Slot is accessible"

        reserved = self.get_reserved_slots()

        if len(reserved) >= len(blocking):
            return True, blocking, \
                f"{len(blocking)} slot(s) need relocation"
        else:
            return False, blocking, \
                f"Not enough reserved slots! " \
                f"Need {len(blocking)}, have {len(reserved)}"